from ask_pdf import initialize_rag_system

# Initialize RAG system
qa_chain = initialize_rag_system()

def rag_pipeline(query):
    """Run RAG pipeline and return both answer + contexts for evaluation."""
    if not qa_chain:
        return {"answer": None, "contexts": [], "error": "RAG system is not initialized properly."}

    try:
        # Step 1: Retrieve documents (depends on your chain API)
        # Many LangChain-style retrievers allow `qa_chain.retriever.get_relevant_documents(query)`
        retrieved_docs = qa_chain.retriever.get_relevant_documents(query)
        retrieved_contexts = [doc.page_content for doc in retrieved_docs]

        # Step 2: Generate answer
        result = qa_chain.invoke({"query": query})

        return {
            "answer": result["result"],     # The LLM output
            "contexts": retrieved_contexts  # The retrieved chunks
        }
    except Exception as e:
        return {"answer": None, "contexts": [], "error": str(e)}
