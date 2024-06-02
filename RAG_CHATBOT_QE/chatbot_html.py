from flask import Flask, request, jsonify, render_template
import json
from pathlib import Path
import numpy as np
import openai
import sqlite3
import faiss
import os
from openai import OpenAI
from dotenv import load_dotenv
from chatbot_html import register, login, perform_rag_request, inquire_more_information

app = Flask(__name__)
load_dotenv()

client = OpenAI()
client.api_key = os.getenv('OPENAI_API_KEY')

model_large = "text-embedding-3-large"
model_small = "text-embedding-3-small"
index_path_ABPR = "data/ABPR/articles_large.index"
json_path_ABPR = "data/ABPR/articles_large.json"
index_path_ABPR_small = "data/ABPR/articles.index"
json_path_ABPR_small = "data/ABPR/articles.json"
index_path_ARG = "data/ARG/articles.index"
json_path_ARG = "data/ARG/articles_embedded.json"
index_path_KAR = "data/KAR/articles.index"
json_path_KAR = "data/KAR/articles_embedded.json"

# Database setup
conn = sqlite3.connect('chatbot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                response TEXT,
                action TEXT,
                articles TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

conn.commit()

# User authentication functions
def register(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return "Registration successful!"
    except sqlite3.IntegrityError:
        return "Username already exists. Please choose a different username."

def login(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    if user:
        return user[0]  # Return user_id
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def handle_register():
    data = request.json
    username = data['username']
    password = data['password']
    result = register(username, password)
    return jsonify(result=result)

@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    username = data['username']
    password = data['password']
    user_id = login(username, password)
    if user_id:
        return jsonify(result="Login successful!", user_id=user_id)
    else:
        return jsonify(result="Invalid username or password.")

@app.route('/respond', methods=['POST'])
def respond():
    data = request.json
    user_id = data['user_id']
    message = data['message']
    response, filtered_articles = perform_rag_request(message, data['filter_values'], data.get('additional_context', ""))
    #log_interaction(user_id, message, response, filtered_articles, "perform_rag_request")
    return jsonify(response=response)

# Add other backend functions as needed

if __name__ == "__main__":
    app.run(debug=True)
