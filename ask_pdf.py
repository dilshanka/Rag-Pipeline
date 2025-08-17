
import logging
import os
import pickle
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA


from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Re-ranking
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)


#  Load or initialize embeddings

def load_or_initialize_embeddings():
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


#  Cross-encoder re-ranking

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(query, docs):
    """Re-rank retrieved documents by semantic relevance."""
    pairs = [[query, d.page_content] for d in docs]
    scores = cross_encoder.predict(pairs)
    sorted_docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)]
    return sorted_docs


#  Initialize  RAG system

def initialize_rag_system():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY not found in .env")
        return None

    embeddings = load_or_initialize_embeddings()

    # Connect to ChromaDB
    persist_directory = "./legal_db"
    if not os.path.exists(persist_directory):
        logging.error("ChromaDB not found!")
        return None

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="legal_docs",
    )

    if vector_db._collection.count() == 0:
        logging.error("No documents found in ChromaDB!")
        return None

    logging.info(f"Found {vector_db._collection.count()} documents in ChromaDB")

    # Load all docs for BM25 keyword search
    logging.info("Loading documents for BM25 keyword search...")
    all_docs = vector_db.similarity_search("placeholder", k=vector_db._collection.count())
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = 5

    # Dense retriever
    dense_retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    # Hybrid retrieval
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, dense_retriever],
        weights=[0.5, 0.5]
    )

    # Multi-query retrieval
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=1024)
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=hybrid_retriever,
        llm=llm
    )

    # Contextual compression
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=multi_query_retriever
    )

    # Prompt with citations
    prompt_template = """
    You are a legal assistant. Use ONLY the provided legal documents to answer.
    Include source citations in square brackets after each relevant fact.
    If unsure, say: "Not enough information."

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=compression_retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True,
    )

    logging.info("Advanced Legal Document RAG System initialized")
    return qa_chain


#  Ask questions loop

def ask_questions(qa_chain):
    logging.info("📚 Advanced Legal Document Q&A Ready!")
    logging.info("Type 'exit' to quit")

    while True:
        question = input("\nEnter your question: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            break

        try:
            # Retrieve
            logging.info("Retrieving documents...")
            result = qa_chain.invoke({"query": question})

            # Re-rank docs
            reranked_docs = rerank(question, result["source_documents"])

            # Display answer
            logging.info("\n Answer:")
            logging.info(result["result"])

            # Show top sources
            logging.info("\n Top Sources:")
            for i, doc in enumerate(reranked_docs[:3], 1):
                source = doc.metadata.get("source", "Unknown")
                logging.info(f"{i}. {source}")

        except Exception as e:
            logging.error(f" Error: {e}")




def main():
    qa_chain = initialize_rag_system()
    if qa_chain:
        ask_questions(qa_chain)

if __name__ == "__main__":
    main()
