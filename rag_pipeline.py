
from ask_pdf import initialize_rag_system


qa_chain = initialize_rag_system()

def rag_pipeline(query):
    """Invoke RAG with a user question."""
    if not qa_chain:
        return "RAG system is not initialized properly."

    try:
        result = qa_chain.invoke({"query": query})
        return result["result"]
    except Exception as e:
        return f"Error: {e}"
