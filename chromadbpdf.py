
import os
import io
import re
import uuid
import base64
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import fitz 
from PIL import Image
import torch

from dotenv import load_dotenv
load_dotenv()  

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Vision OCR 
OPENAI_OCR_MODEL = os.getenv("OPENAI_OCR_MODEL", "gpt-4o-mini")  
OCR_DPI = int(os.getenv("OCR_DPI", "220"))                       
OCR_MAX_RETRIES = 3
OCR_BACKOFF = 2.0  
OCR_PROMPT = os.getenv(
    "OCR_PROMPT",
    "Extract all legible body text from this legal page. Preserve reading order. "
    "Ignore repeated headers/footers and watermarks. Return plain UTF-8 text."
)

try:
    from openai import OpenAI
    openai_client: Optional["OpenAI"] = OpenAI()  
    _has_openai = True
except Exception as _e:
    logging.warning("OpenAI SDK not available or OPENAI_API_KEY not set. OCR fallback will be disabled.")
    openai_client = None
    _has_openai = False

# ---------------- Helpers ----------------
def normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t\u00A0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def render_page_png(page: fitz.Page, dpi: int = OCR_DPI) -> bytes:
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

def ocr_png_with_openai(img_bytes: bytes) -> str:
    """OCR a PNG image using OpenAI Vision. Returns normalized text or '' on failure."""
    if not _has_openai:
        return ""
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    last_err = None
    for attempt in range(1, OCR_MAX_RETRIES + 1):
        try:
            resp = openai_client.chat.completions.create(
                model=OPENAI_OCR_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": "You are an OCR assistant for legal documents. Return only extracted text."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": OCR_PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}" }}
                        ]
                    }
                ]
            )
            text = resp.choices[0].message.content or ""
            return normalize_ws(text)
        except Exception as e:
            last_err = e
            if attempt < OCR_MAX_RETRIES:
                backoff = (OCR_BACKOFF ** (attempt - 1))
                logging.warning(f"OCR attempt {attempt} failed ({e}). Retrying in {backoff:.1f}s...")
                import time; time.sleep(backoff)
    logging.error(f"OCR failed after {OCR_MAX_RETRIES} attempts: {last_err}")
    return ""


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from a PDF, page by page.
    - Uses PyMuPDF text first.
    - Falls back to OpenAI OCR if the page text is empty/very short (scanned).
    """
    try:
        doc = fitz.open(pdf_path)
        text_pages = []
        for page_num, page in enumerate(doc, start=1):
            text = (page.get_text("text") or "").strip()

            # do OCR for scanned images.
            if len(text) < 25:
                try:
                    img_bytes = render_page_png(page, dpi=OCR_DPI)
                    ocr_text = ocr_png_with_openai(img_bytes)
                    if len(ocr_text) > len(text):
                        text = ocr_text
                except Exception as e:
                    logging.warning(f"OCR fallback failed for page {page_num} in {pdf_path}: {e}")

            if text.strip():
                text_pages.append((page_num, text.strip()))
        doc.close()
        return text_pages
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return []

def process_pdf(pdf_file: str, pdf_dir: str, text_splitter: RecursiveCharacterTextSplitter):
    """
    Extract and split PDF text into chunks. Adds richer metadata and stable IDs.
    """
    full_path = os.path.join(pdf_dir, pdf_file)
    pages = extract_text_from_pdf(full_path)

    # stable per-file document_id based on file path URI
    try:
        document_id = uuid.uuid5(uuid.NAMESPACE_URL, Path(full_path).resolve().as_uri()).hex
    except Exception:
        document_id = uuid.uuid4().hex

    chunks, metadata_list, ids = [], [], []
    upload_date = datetime.now().strftime("%Y-%m-%d")

    for page_num, text in pages:
        split_chunks = [c.strip() for c in text_splitter.split_text(text)]
        for i, chunk in enumerate(split_chunks):
            if len(chunk) < 30:  
                continue
            chunks.append(chunk)
            metadata_list.append({
                "source": pdf_file,
                "source_path": str(Path(full_path).resolve()),
                "page_number": page_num,
                "chunk_id": i,
                "document_id": document_id,
                "document_type": "Legal Document",  
                "jurisdiction": "Unknown",          
                "upload_date": upload_date
            })
            ids.append(f"{document_id}-p{page_num}-c{i}")

    return chunks, metadata_list, ids, document_id

def process_all_pdfs():
    # Config
    pdf_dir = "Ministry Of Defence"
    persist_directory = "./legal_db"
    collection_name = "legal_docs"

    if not os.path.exists(pdf_dir):
        logging.error(f"Directory '{pdf_dir}' does not exist!")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logging.error("No PDF files found!")
        return
    logging.info(f"Found {len(pdf_files)} PDF files to process.")

    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="nlpaueb/legal-bert-base-uncased",
        model_kwargs={"device": device},
    )
    logging.info("LEGAL-BERT model loaded successfully.")

    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    # Open or create ChromaDB
    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    # Collect all chunks
    all_chunks, all_metadatas, all_ids = [], [], []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(lambda pdf: process_pdf(pdf, pdf_dir, text_splitter), pdf_files)

        for pdf_file, (chunks, metadatas, ids, document_id) in zip(pdf_files, results):
            if not chunks:
                logging.warning(f"Skipping empty PDF (no extractable text): {pdf_file}")
                continue
            all_chunks.extend(chunks)
            all_metadatas.extend(metadatas)
            all_ids.extend(ids)
            logging.info(f"Prepared {len(chunks)} chunks from {pdf_file} (document_id={document_id}).")

    if not all_chunks:
        logging.info("No chunks to add. Exiting.")
        return

    logging.info(f"Adding {len(all_chunks)} chunks to ChromaDB (this embeds; may take a while)...")
    vector_db.add_texts(texts=all_chunks, metadatas=all_metadatas, ids=all_ids)

    # Persist once
    vector_db.persist()

    try:
        collection_size = vector_db._collection.count()
    except Exception:
        collection_size = "unknown"
    logging.info(f"Finished processing. Total chunks in ChromaDB: {collection_size}")

if __name__ == "__main__":
    process_all_pdfs()
