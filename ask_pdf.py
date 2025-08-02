
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import pickle

# Setup logging for better traceability
logging.basicConfig(level=logging.INFO)


def load_or_initialize_embeddings():
    """Check if embeddings are already cached; otherwise, initialize them."""
    if os.path.exists('legal_bert_embeddings.pkl'):
        logging.info("Loading cached embeddings...")
        with open('legal_bert_embeddings.pkl', 'rb') as f:
            embeddings = pickle.load(f)
        return embeddings
    else:
        logging.info("Initializing new LEGAL-BERT embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name="nlpaueb/legal-bert-base-uncased")
        with open('legal_bert_embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
        return embeddings


def initialize_rag_system():
    """Initialize the RAG system with LEGAL-BERT + OpenAI GPT"""
    logging.info("Initializing Legal Document RAG System")
    logging.info("=" * 50)

    # Load environment variables from .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        return None

    # Initialize LEGAL-BERT embeddings
    embeddings = load_or_initialize_embeddings()

    # Connect to ChromaDB
    logging.info("Connecting to ChromaDB...")
    persist_directory = "./legal_db"

    if not os.path.exists(persist_directory):
        logging.error("ChromaDB not found!")
        return None

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="legal_docs",
    )

    # Check if data exists
    collection_size = vector_db._collection.count()
    if collection_size == 0:
        logging.error("No documents found in ChromaDB!")
        return None

    logging.info(f"✅ Found {collection_size} documents in ChromaDB")

    # Initialize OpenAI GPT model
    logging.info("Loading OpenAI GPT model...")
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # or "gpt-4o", "gpt-3.5-turbo"
            temperature=0.1,
            max_tokens=1024
        )
        # Test model
        test_response = llm.invoke("Hello")
        logging.info("✅ OpenAI GPT model loaded successfully")
    except Exception as e:
        logging.error(f"Error loading OpenAI GPT model: {e}")
        return None

    # Custom prompt for legal docs
    prompt_template = """
    You are a legal document assistant. Use the following legal document context to answer the question.
    Be precise, cite relevant sections, and provide professional legal insights.
    If you don't know the answer based on the context, say "I don't have enough information in the provided documents."
    
    Context: {context}
    
    Question: {question}
    
    Answer:
    """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Create retrieval QA chain
    logging.info("Creating RAG chain...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},  # Increased k value for better accuracy in retrieval
        ),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True,
    )

    logging.info("✅ RAG system initialized successfully!")
    return qa_chain


def ask_questions(qa_chain):
    """Interactive question-answer loop"""
    logging.info(f"\Legal Document Q&A System Ready!")
    logging.info("=" * 50)
    logging.info("Ask questions about your legal documents")
    logging.info("Type 'exit' or 'quit' to stop")
    logging.info("=" * 50)

    while True:
        question = input("\nEnter your question: ").strip()

        if question.lower() in ["exit", "quit", "q"]:
            logging.info("👋 Goodbye!")
            break

        if not question:
            continue

        try:
            logging.info("\n🔍 Searching documents...")
            result = qa_chain.invoke({"query": question})

            # Display answer
            logging.info(f"\n📖 Answer:")
            logging.info("-" * 40)
            logging.info(result["result"])

            # Display sources
            logging.info(f"\n📂 Sources:")
            logging.info("-" * 40)
            for i, doc in enumerate(result["source_documents"], 1):
                source = doc.metadata.get("source", "Unknown")
                chunk_id = doc.metadata.get("chunk_id", "N/A")
                content_preview = (
                    doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                )

                logging.info(f"{i}. 📄 {source} (Chunk {chunk_id})")
                logging.info(f"   📝 {content_preview}\n")

        except Exception as e:
            logging.error(f"Error processing question: {e}")


def main():
    logging.info("📑 Legal Document RAG System")
    logging.info("LEGAL-BERT + ChromaDB + OpenAI GPT")
    logging.info("=" * 60)

    qa_chain = initialize_rag_system()

    if qa_chain is None:
        logging.error("\nFailed to initialize RAG system!")
        return

    ask_questions(qa_chain)


if __name__ == "__main__":
    main()
