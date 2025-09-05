# 🎓 Academic Study Assistant

An AI-powered study assistant for university students that can answer questions about course materials using advanced RAG (Retrieval-Augmented Generation) technology.

## Features

- **Smart Document Processing**: Handles PDFs, lecture notes, textbooks, and research papers
- **Advanced RAG System**: Uses hybrid retrieval (semantic + keyword search) for accurate answers
- **Student-Friendly Interface**: Web-based chat interface designed for students
- **Source Citations**: Shows which documents and pages answers come from
- **Multiple Document Types**: Automatically categorizes content (lecture notes, textbooks, research papers)
- **OCR Support**: Can extract text from scanned PDFs using AI vision

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 2. Prepare Your Documents

```bash
# Create directory for your course materials
mkdir university_documents

# Add your PDF files (lectures, textbooks, papers, etc.)
# Example structure:
# university_documents/
#   ├── lecture_1_introduction.pdf
#   ├── textbook_chapter_3.pdf
#   ├── research_paper_ai.pdf
#   └── assignment_guidelines.pdf
```

### 3. Process Documents

```bash
# This will create embeddings and store them in ChromaDB
python chromadbpdf.py
```

### 4. Start the Study Assistant

```bash
# Start the API server
python rag_api.py

# In another terminal, open the web interface
open student_interface.html
```

### 5. Start Chatting!

Open `student_interface.html` in your browser and start asking questions about your course materials!

## Usage Examples

### Web Interface
- Open `student_interface.html` in your browser
- Enter your name (optional)
- Ask questions like:
  - "What are the main concepts in this chapter?"
  - "Can you explain machine learning in simpler terms?"
  - "What should I focus on for the exam?"

### Command Line Interface
```bash
# Run the interactive Q&A
python ask_pdf.py
```

### API Usage
```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the main topic of this chapter?", "student_name": "Alex"}'
```

## File Structure

```
Rag-Pipeline/
├── chromadbpdf.py          # Document processing and embedding creation
├── ask_pdf.py             # Core RAG system with advanced retrieval
├── rag_pipeline.py        # Simple wrapper for the RAG system
├── rag_api.py             # FastAPI web service
├── view_embeddings.py     # Database inspection utility
├── student_interface.html # Web-based chat interface
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── university_documents/  # Your course materials (create this)
└── academic_db/          # ChromaDB storage (created automatically)
```

## Configuration

### Environment Variables (.env file)
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_OCR_MODEL=gpt-4o-mini  # Optional: for OCR of scanned PDFs
OCR_DPI=220                   # Optional: DPI for OCR processing
```

### Document Processing Settings
Edit `chromadbpdf.py` to customize:
- `pdf_dir`: Directory containing your documents
- `chunk_size`: Size of text chunks (default: 1000 characters)
- `chunk_overlap`: Overlap between chunks (default: 200 characters)

## Advanced Features

### Hybrid Retrieval
The system combines:
- **Dense Retrieval**: Semantic similarity using embeddings
- **BM25 Retrieval**: Keyword-based search
- **Multi-Query Expansion**: Generates multiple query variations
- **Contextual Compression**: Filters to most relevant content
- **Re-ranking**: Final relevance scoring

### Document Types
Automatically categorizes documents:
- `lecture_notes`: Files with "lecture" in the name
- `textbook`: Files with "textbook" in the name  
- `research_paper`: Files with "paper" in the name
- `general`: All other documents

### OCR Support
For scanned PDFs, the system:
- Detects low-text pages
- Uses OpenAI Vision API for OCR
- Falls back gracefully if OCR fails

## Troubleshooting

### Common Issues

1. **"Academic database not found"**
   - Run `python chromadbpdf.py` first to process your documents

2. **"No documents found in ChromaDB"**
   - Make sure you have PDF files in the `university_documents/` directory
   - Check that the PDFs contain extractable text

3. **API connection errors**
   - Make sure `python rag_api.py` is running
   - Check that port 8000 is available

4. **OpenAI API errors**
   - Verify your API key in the `.env` file
   - Check your OpenAI account has sufficient credits

### Database Inspection
```bash
# View your processed documents and embeddings
python view_embeddings.py
```

## Customization

### Adding New Document Types
Edit the `content_type` logic in `chromadbpdf.py`:
```python
"content_type": "lecture_notes" if "lecture" in pdf_file.lower() 
    else "textbook" if "textbook" in pdf_file.lower() 
    else "research_paper" if "paper" in pdf_file.lower() 
    else "assignment" if "assignment" in pdf_file.lower()  # Add new type
    else "general"
```

### Modifying the AI Assistant's Personality
Edit the prompt template in `ask_pdf.py` to change how the assistant responds.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
