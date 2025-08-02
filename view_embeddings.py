import chromadb
import numpy as np
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def view_all_embeddings():
 
    
    print(" ChromaDB Embedding Viewer")
    
    
    try:
        # Connect to ChromaDB
        persist_directory = "./legal_db"
        
      
        embeddings = HuggingFaceEmbeddings(
            model_name="nlpaueb/legal-bert-base-uncased"
        )
        
        # Connect to existing vector store
        vector_db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="legal_docs"
        )
        
        print("Connected to ChromaDB successfully")
        
        # Get collection info
        collection = vector_db._collection
        total_docs = collection.count()
        print(f"📊 Total documents: {total_docs}")
        
        if total_docs == 0:
            print(" No documents found in the collection!")
            return
        
        # Get all data
        results = collection.get(
            include=['embeddings', 'documents', 'metadatas']
        )
        
        embeddings_array = np.array(results['embeddings'])
        print(f"Vector dimensions: {embeddings_array.shape[1]}")
        print(f"Storage size: {embeddings_array.nbytes / (1024*1024):.2f} MB")
        
        # Group by source
        sources = {}
        for i, metadata in enumerate(results['metadatas']):
            source = metadata.get('source', 'Unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(i)
        
        print(f"\n Documents by source:")
        for source, indices in sources.items():
            print(f" {source}: {len(indices)} chunks")
        
        # Show sample embeddings
        print(f"\nSample embeddings:")
        for i in range(min(5, len(results['documents']))):
            doc = results['documents'][i]
            embedding = results['embeddings'][i]
            metadata = results['metadatas'][i]
            
            doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
            print(f"\n--- Sample {i+1} ---")
            print(f"Source: {metadata.get('source', 'Unknown')}")
            print(f"Text: {doc_preview}")
            print(f"Embedding (first 10 dims): {embedding[:10]}")
            print(f"Vector magnitude: {np.linalg.norm(embedding):.4f}")
        
        # Embedding statistics
        print(f"\n Embedding Statistics:")
        magnitudes = [np.linalg.norm(emb) for emb in results['embeddings']]
        print(f"   Mean magnitude: {np.mean(magnitudes):.4f}")
        print(f"   Std magnitude: {np.std(magnitudes):.4f}")
        print(f"   Min value: {np.min(embeddings_array):.4f}")
        print(f"   Max value: {np.max(embeddings_array):.4f}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    view_all_embeddings()
