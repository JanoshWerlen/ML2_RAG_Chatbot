import openai
import os
from openai import OpenAI

# Set your OpenAI API key
from dotenv import load_dotenv
# Set your OpenAI API key

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
# Function to generate embeddings using the OpenAI API
import json
import numpy as np
import faiss
import openai

def get_embedding(text, tags, model="text-embedding-3-large"):
    text = text.replace("\n", " ")
    combine = text + " " .join(tags)
    return openai.embeddings.create(input=[combine], model=model).data[0].embedding

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to save JSON data to a file
def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

file_path = 'ARG/articles.json'
data = load_json(file_path)
file_path_new = 'ARG/articles_embedded.json'

# Assuming you have your data loaded and structured
for article in data:
    article_text = article['text']
    article_tags = article['metadata']['tags']
    article['embedding'] = get_embedding(article_text, article_tags)

# Save the updated data with embeddings back to the JSON file
save_json(data, file_path_new)

# Extract embeddings from the articles
embeddings = np.array([article['embedding'] for article in data]).astype('float32')

# Create a base index - L2 distance
base_index = faiss.IndexFlatL2(embeddings.shape[1])

# Create an IndexIDMap
index = faiss.IndexIDMap(base_index)

# IDs for the articles
ids = np.array([i for i in range(len(data))], dtype='int64')  # Ensure IDs are int64

# Add vectors and their IDs to the index
index.add_with_ids(embeddings, ids)

# Save the index to disk
faiss.write_index(index, "ARG/articles.index")


# Extract embeddings from the articles
embeddings = np.array([article['embedding'] for article in data]).astype('float32')

# Create a base index - L2 distance
base_index = faiss.IndexFlatL2(embeddings.shape[1])

# Create an IndexIDMap
index = faiss.IndexIDMap(base_index)

# IDs for the articles
ids = np.array([i for i in range(len(data))], dtype='int64')  # Ensure IDs are int64

# Add vectors and their IDs to the index
index.add_with_ids(embeddings, ids)

# Save the index to disk
faiss.write_index(index, "articles.index")
