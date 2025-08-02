
import os
import fitz  # PyMuPDF
import concurrent.futures
import torch
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


# Setup logging for better traceability
logging.basicConfig(level=logging.INFO)


def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text")  # Use "text" mode for faster extraction
        doc.close()
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def process_pdf(pdf_file, pdf_dir, text_splitter):
    """Process a single PDF: extract text and split into chunks"""
    full_path = os.path.join(pdf_dir, pdf_file)
    text = extract_text_from_pdf(full_path)
    if text:
        chunks = text_splitter.split_text(text)
        return chunks, pdf_file
    return [], pdf_file


def embed_text_chunks_in_batches(chunks, embeddings, batch_size=64):
    """Embed text chunks in batches for efficiency"""
    embeddings_list = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embeddings_list.extend(embeddings.embed_documents(batch))
    return embeddings_list


def process_all_pdfs():
    """Process all PDFs in the Ministry Of Defence folder"""
    # Configuration
    pdf_dir = "Ministry Of Defence"
    persist_directory = "./legal_db"

    logging.info("Starting PDF processing with LEGAL-BERT embeddings...")

    # Check for GPU availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")

    # Load LEGAL-BERT model
    embeddings = HuggingFaceEmbeddings(
        model_name="nlpaueb/legal-bert-base-uncased",
        model_kwargs={"device": device},
    )
    logging.info("LEGAL-BERT model loaded successfully!")

    if not os.path.exists(pdf_dir):
        logging.error(f"Directory {pdf_dir} does not exist!")
        return

    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    logging.info(f"Found {len(pdf_files)} PDF files")

    if not pdf_files:
        logging.error("No PDF files found!")
        return

    # Text splitter setup
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    # Process each PDF in parallel using ThreadPoolExecutor
    all_texts = []
    all_metadatas = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(lambda pdf: process_pdf(pdf, pdf_dir, text_splitter), pdf_files)

        for chunks, filename in results:
            all_texts.extend(chunks)
            all_metadatas.extend(
                [{"source": filename, "chunk_id": i} for i in range(len(chunks))]
            )

    if not all_texts:
        logging.error("No text chunks to process!")
        return

    # Embed text chunks in batches
    logging.info("Embedding text chunks in batches...")
    all_embeddings = embed_text_chunks_in_batches(all_texts, embeddings)
    logging.info("Text chunks embedded successfully!")

    # Create or load ChromaDB vector store
    logging.info("Creating ChromaDB vector store...")
    if os.path.exists(persist_directory):
        logging.info(f"Loading existing ChromaDB from {persist_directory}")
        vector_db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    else:
        logging.info("Creating new ChromaDB...")
        # Directly create vector store with texts, embeddings, and metadata
        vector_db = Chroma.from_texts(
            texts=all_texts,
            embedding=embeddings,
            metadatas=all_metadatas,
            persist_directory=persist_directory,
            collection_name="legal_docs",
        )

    # Verify storage
    collection_size = vector_db._collection.count()
    logging.info(f"Total documents in ChromaDB: {collection_size}")

    logging.info("PDF processing completed successfully!")


if __name__ == "__main__":
    process_all_pdfs()
