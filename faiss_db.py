import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# FAISS database file
FAISS_INDEX_FILE = "faiss_index.bin"

# Initialize FAISS index
def load_faiss_index():
    if os.path.exists(FAISS_INDEX_FILE):
        print("Loading existing FAISS index...")
        index = faiss.read_index(FAISS_INDEX_FILE)
    else:
        print("Creating new FAISS index...")
        index = faiss.IndexFlatL2(384)  # 384-dim for MiniLM embeddings
        faiss.write_index(index, FAISS_INDEX_FILE)  # Save the new index to file
    return index

faiss_index = load_faiss_index()
ef_value_store = {}  # Dictionary to map FAISS vectors to EF values

def store_ef_value(text, ef_value, doc_name):
    """Stores EF values as embeddings in FAISS."""
    global faiss_index

    vector = embedding_model.encode([text])[0]
    
    # Normalize the vector (Important for better matching)
    vector = vector / np.linalg.norm(vector)  
    vector = np.array([vector], dtype=np.float32)

    if vector.shape[0] != faiss_index.d:
        print("Error: FAISS index dimension mismatch!")
        return

    # Store EF value in FAISS
    faiss_index.add(vector)
    ef_value_store[len(ef_value_store)] = (ef_value, doc_name)

    # Save FAISS index
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)
    print(f"Stored EF Value: {ef_value} | Document: {doc_name} | FAISS Index Size: {faiss_index.ntotal}")

def retrieve_ef_value(text, top_k=1):
    """Retrieves the most similar EF value from FAISS."""
    if faiss_index.ntotal == 0:
        print("FAISS Index is empty. No EF values stored.")
        return None  # No stored values yet

    vector = embedding_model.encode([text])[0]
    vector = vector / np.linalg.norm(vector)  # Normalize the vector
    vector = np.array([vector], dtype=np.float32)

    _, indices = faiss_index.search(vector, top_k)

    retrieved_ef_values = [ef_value_store[i] for i in indices[0] if i in ef_value_store]

    return retrieved_ef_values[0] if retrieved_ef_values else None