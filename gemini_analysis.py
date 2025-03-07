import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# ✅ Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ FAISS database file
FAISS_INDEX_FILE = "faiss_index.bin"

# ✅ Initialize FAISS index
def load_faiss_index():
    if os.path.exists(FAISS_INDEX_FILE):
        print("Loading existing FAISS index...")
        index = faiss.read_index(FAISS_INDEX_FILE)
    else:
        print("Creating new FAISS index...")
        index = faiss.IndexFlatL2(384)  # 384-dim for MiniLM embeddings
    return index

faiss_index = load_faiss_index()
ef_value_store = {}  # Dictionary to map FAISS vectors to EF values

def store_ef_value(text, ef_value):
    """Stores EF values as embeddings in FAISS."""
    global faiss_index

    vector = embedding_model.encode([text])[0]
    
    # ✅ Normalize the vector (Important for better matching)
    vector = vector / np.linalg.norm(vector)  
    vector = np.array([vector], dtype=np.float32)

    if vector.shape[1] != faiss_index.d:
        print("Error: FAISS index dimension mismatch!")
        return

    # ✅ Store EF value in FAISS
    faiss_index.add(vector)
    ef_value_store[len(ef_value_store)] = ef_value

    # ✅ Save FAISS index
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)
    print(f"Stored EF Value: {ef_value} | FAISS Index Size: {faiss_index.ntotal}")
