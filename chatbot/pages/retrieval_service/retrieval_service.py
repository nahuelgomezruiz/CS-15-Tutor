import os
import faiss
import numpy as np
import json
from flask import Flask, request, jsonify


app = Flask(__name__)


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the data directory
data_dir = os.path.join(current_dir, "data")

# Load the FAISS index
index_path = os.path.join(data_dir, "faiss_index.index")
index = faiss.read_index(index_path)

# Load the documents and filenames
with open(os.path.join(data_dir, "documents.json"), "r", encoding="utf-8") as f:
    data = json.load(f)
    documents = data["documents"]
    filenames = data["filenames"]

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    # Expecting a float32 embedding array and an optional k parameter
    embedding = np.array(data["embedding"], dtype=np.float32)
    k = data.get("k", 3)
    
    # Reshape embedding to 2D array for FAISS (1, d)
    embedding = np.expand_dims(embedding, axis=0)
    distances, indices = index.search(embedding, k)
    
    # Retrieve corresponding documents and filenames
    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # Skip invalid indices
            results.append({
                "document": documents[idx],
                "filename": filenames[idx],
                "distance": float(distances[0][i])  # Convert numpy float to Python float
            })
    
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(port=5050)