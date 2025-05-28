from pathlib import Path
import os
from openai import OpenAI
import numpy as np
import faiss
import json
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to generate embeddings
def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# folder with transcripts (stored as a {filename: filedata} dictionary):
folder_path = "data/text files"  # Updated path to use the correct text files directory

print(f"Looking for files in: {folder_path}")
files = sorted(Path(folder_path).glob("*.txt"))  # sort files in docs directory
print(f"Found {len(files)} files")

embedding_list = []
documents = []
filenames = []

# Loop through files in sorted order
for file in files:
    print(f"Processing file: {file}")
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
        try:
            embedding = get_embedding(content)
            embedding_list.append(embedding)
            documents.append(content)
            filenames.append(file.name)
            print(f"Successfully processed {file.name}")
        except Exception as e:
            print(f"Error processing {file.name}: {str(e)}")

print(f"Total embeddings created: {len(embedding_list)}")

# Convert to FAISS index
if not embedding_list:
    raise ValueError("No embeddings were created. Check if files exist and API calls succeeded.")

embedding_array = np.array(embedding_list, dtype=np.float32)
d = embedding_array.shape[1]

index = faiss.IndexFlatL2(d)
index.add(embedding_array)

print("Number of embeddings indexed:", index.ntotal)

# Create output directory if it doesn't exist
output_dir = "chatbot/pages/retrieval_service/data"
os.makedirs(output_dir, exist_ok=True)

# Save index
faiss.write_index(index, os.path.join(output_dir, "faiss_index.index"))

# Save documents and filenames
with open(os.path.join(output_dir, "documents.json"), "w", encoding="utf-8") as f:
    json.dump({
        "documents": documents,
        "filenames": filenames
    }, f, ensure_ascii=False, indent=2)

print(f"Saved index and documents to {output_dir}")
