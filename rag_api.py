# Academic Study Assistant API

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import rag_pipeline 
from fastapi.responses import PlainTextResponse
import logging
import os
import subprocess
from pathlib import Path

app = FastAPI(
    title="Academic Study Assistant",
    description="AI-powered study assistant for university students",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Process new documents on startup"""
    logging.info("🚀 Starting Academic Study Assistant...")
    logging.info("📚 Checking for new documents...")
    
    # Check and process new documents
    if check_and_process_new_documents():
        logging.info("✅ Document processing completed")
    else:
        logging.info("ℹ️ No new documents to process or processing skipped")
    
    logging.info("🎓 Academic Study Assistant is ready!")

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    student_name: str = "Student"  # Optional student name for personalization

class ChatResponse(BaseModel):
    response: str
    sources: list = []
    success: bool = True

def check_and_process_new_documents():
    """Check for new documents and process them if found"""
    try:
        # Check if university_documents directory exists
        docs_dir = Path("university_documents")
        if not docs_dir.exists():
            logging.info("No university_documents directory found")
            return False
        
        # Get list of PDF files in the directory
        pdf_files = list(docs_dir.glob("*.pdf"))
        if not pdf_files:
            logging.info("No PDF files found in university_documents")
            return False
        
        # Check if academic_db exists (indicates previous processing)
        academic_db = Path("academic_db")
        if not academic_db.exists():
            logging.info("No existing academic_db found, processing all documents...")
            return process_documents()
        
        # Check modification times to see if any PDFs are newer than the last processing
        # For simplicity, we'll always process if there are PDFs and academic_db exists
        # In a more sophisticated version, you could track timestamps
        logging.info(f"Found {len(pdf_files)} PDF files, processing documents...")
        return process_documents()
        
    except Exception as e:
        logging.error(f"Error checking for new documents: {e}")
        return False

def process_documents():
    """Run the document processing script"""
    try:
        logging.info("Starting document processing...")
        result = subprocess.run(
            ["python", "chromadbpdf.py"], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            logging.info("Document processing completed successfully")
            return True
        else:
            logging.error(f"Document processing failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error running document processing: {e}")
        return False

@app.get("/")
async def root():
    return {
        "message": "🎓 Academic Study Assistant API",
        "description": "Ask questions about your course materials!",
        "endpoints": {
            "/chat": "POST - Ask questions about your documents",
            "/health": "GET - Check if the system is ready",
            "/process-documents": "POST - Manually process new documents"
        }
    }

@app.get("/health")
async def health_check():
    try:
        # Test if RAG system is working
        test_response = rag_pipeline("test")
        return {
            "status": "healthy",
            "message": "Academic Study Assistant is ready!",
            "rag_system": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"System not ready: {str(e)}")

@app.post("/process-documents")
async def process_documents_endpoint():
    """Manually trigger document processing"""
    try:
        logging.info("Manual document processing requested...")
        if process_documents():
            return {
                "status": "success",
                "message": "Documents processed successfully!",
                "processed": True
            }
        else:
            return {
                "status": "error", 
                "message": "Document processing failed",
                "processed": False
            }
    except Exception as e:
        logging.error(f"Error in manual document processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Please provide a question")
        
        # Add student context to the question
        personalized_question = f"Hi! I'm {request.student_name}. {request.message}"
        
        response = rag_pipeline(personalized_question)
        
        return ChatResponse(
            response=response,
            sources=[],  # Could be enhanced to return source documents
            success=True
        )
    except Exception as e:
        logging.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing your question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
