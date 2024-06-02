import json
import numpy as np
import openai
import sqlite3
from getpass import getpass
from openai import OpenAI
import faiss

# Configure OpenAI API key
client = OpenAI()
client.api_key = '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'


#model = "text-embedding-3-large"
model = "text-embedding-3-small"
#index_path = "data/ABPR/articles_large.index"
#json_path = "data/ABPR/articles.json"
index_path = "data/ARG/articles_incl_ARG.index"
json_path = "data/ARG/articles_incl_ARG_embedded.json"

# Database setup
conn = sqlite3.connect('chatbot.db')
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

conn.commit()

# User authentication functions
def register(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        print("Registration successful!")
    except sqlite3.IntegrityError:
        print("Username already exists. Please choose a different username.")

def login(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, password))
    user = c.fetchone()
    if user:
        print("Login successful!")
        return user[0]  # Return user_id
    else:
        print("Invalid username or password.")
        return None

def get_embedding(text, tags, model=model):
    text = text.replace("\n", " ")
    combine = text + " " .join(tags)
    return openai.embeddings.create(input=[combine], model=model).data[0].embedding

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to save JSON data to a file
data = load_json(json_path)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def filter_entries(attribute_values):
    output_path="filtered_articles.json"
    print("\n filter data nach " + str(attribute_values) + "\n")
    attribute_name = "Gesetzestext"
    
    # Read the existing JSON data from the input file
    with open(json_path, 'r') as file:
        json_data = json.load(file)
    
    # Initialize a list to hold the filtered entries
    filtered_entries = []

    # Check if json_data is a list
    if isinstance(json_data, list):
        for entry in json_data:
            # Check if 'metadata' exists and is a dictionary in each entry
            if 'metadata' in entry and isinstance(entry['metadata'], dict):
                # Add to filtered list if the attribute matches any value in the attribute_values list
                if entry['metadata'].get(attribute_name) in attribute_values:
                    filtered_entries.append(entry)
            else:
                print(f"Error: 'metadata' key not found or is not a dictionary in entry {entry}.")
    else:
        print("Error: JSON data is not a list of entries.")
    
    # Write the filtered entries to the output file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(filtered_entries, file, indent=4, ensure_ascii=False)
    
    # Return the output path of the filtered JSON file
    return output_path



def refine_query(query):
    print("\nOriginales Query: " + query + "\n")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Erweitere die User Anfrage: '{query}', mit Suchbegriffen, damit die Frage möglichst gute RAG ergebnisse liefert. Der erweiterte Anfrage soll ich immer auf den Kontext einer Anstellung am Stadtspital Zürich in der Schweiz beziehen."},
        ]
    )
    response = response.choices[0].message.content
    print("\nimproving query... \n")
    print("\nimproved query: " + response + "\n")
    return response

def generate_query_embedding(query):
    return get_embedding(query, [])

def get_response_string(refind_query, filter_values):
    query_embedding = np.array(generate_query_embedding(
        refind_query)).astype('float32').reshape(1, -1)
    
    index = faiss.read_index(index_path)

    # Load the index from disk
    
    if filter_values:
        filtered_json = filter_entries(filter_values)
        data = load_json(filtered_json)
    else:
        data = load_json(json_path)

    data = load_json(json_path)        

    # Perform the search
    k = 5  # Number of nearest neighbors to retrieve
    distances, indices = index.search(query_embedding, k)

    # Ensure 'indices' is a list of integers and not out of range
    indices = indices[0]

    # Retrieve the matching articles
    matching_articles = [data[i] for i in indices if i < len(data)]  # Direct access by index
    response_string = ""
    # Print the matching articles
    for article in matching_articles:
        response_string += f"Article Number: {article['article_number']}, Gesetzestext: {article['metadata'].get('Gesetzestext')}, Title: {article['title']},\n Text: {article['text']}\n"
    print("\nResponse: " + response_string + "\n")
    print("\nFinding relevant articles... \n")
    print("\nRelevant Articles found... \n")
    return response_string


def perform_rag_request(message, filter_values):
    print("\n performing RAG based on query: " + str(message) + "\n")

    refind_query = refine_query(message)
    response_string = get_response_string(refind_query, filter_values)

    system_query = f"""Du bist ein HR-Assistent des Stadtspitals Zürich, welcher Fragen von Angestellten beantwortet. Antworte basierend auf den Inhalten in den folgenden Artikeln: '{response_string}'.
    Antworte professionell und kurz ohne Begrüssung oder Verabschiedung. Verwende direkte Zitate aus den Artikeln und setze diese in Anführungszeichen. Gib am Ende eine Liste aller relevanten Artikel und Artikeltitel an. Bei Fragen welche überhaupt nichts mit der Arbeit zutun haben, lenke den zurück zum Thema. """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"{system_query}"},
            {"role": "user", "content": f"{refind_query}"}
        ]
    )
    response = response.choices[0].message.content
    inquired_infos.clear()
    return response

inquired_infos = []
times_inquired = 0

def inquire_more_information(message):
    global times_inquired
    times_inquired += 1
    print(f"\n currently inquired {times_inquired} times... \n")

    print("Aktuelle convo...: " + str(inquired_infos))
    print("\n Inquiring more info... \n")
    system_query = f"Frage genauer nach, was der User wissen will um die originale Anfrage '{message}' zu präzisieren. Akzeptiere nur personalrechtliche Fragen welche um in deiner Rolle als HR-Berater am Stadtspital Zürich relevant sind. Geh davon aus, dass der User immer ein Angestellter des Stadtspitals Zürich ist."
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"{system_query}"},
        ],
        #max_tokens= 100
    )
    response = response.choices[0].message.content
    return response

def decide_action(message):
    print("\n deciding... \n")
    prompt = f"Given the following user message, decide what action should be taken. The options are: perform_rag_request, inquire_more_information, end_conversation. If the User asks a relevant question regarding employment or similar, decide to 'perform_rag_request'. End the conversation if the Questions are mean, unprofessional or insulting.  \n\nUser message: {message}\n\nAction:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"{prompt}"},
        ],
        max_tokens=10,
        stop=['\n']
    )
    
    action = response.choices[0].message.content
    print(f"\n Getroffene Entscheidung: {action} \n")
    return action

def start_convo():
    print("\nFrage Eingeben: ")
    message = input("> ")
    print("Welche Mitarbeitergruppe betirfft deine Frage?")
    print("1: Nicht-Ärzliches Personal")
    print("2: Assistenzärzte")
    print("3: Ärztliches Personal, ausser Assistenzärzte")
    print("4: Unklar / Keine Angabe\n")
    choice = input(">: ")
    if choice == "1":
        filter_values = ["PR", "ABPR"]
    elif choice == "2":
        filter_values = ["AAR", "ARG"]
    elif choice == "3":
        filter_values = ["PR", "ABPR", "KAR"]
    else:
        filter_values = ["PR", "ABPR", "ARG", "AAR", "KAR"]  # Corrected assignment
    print("\n Filter chosen: " + str(filter_values) + "\n")
    return message, filter_values

# Chatbot function
def chatbot(user_id):
    global times_inquired
    keepalive = True
    print("Chatbot initialized. Type 'quit' to exit.")
    while keepalive:
        message, filter_values = start_convo()
        if message.lower() == 'quit':
            break
        inquired_infos.append(message)
        times_inquired = 0
        while True:
            action = decide_action(str(inquired_infos))
            if times_inquired > 3:
                reply = perform_rag_request(str(inquired_infos), filter_values)
                break
            elif action == "end_conversation":
                keepalive = False
                print("Bot: Ending the conversation.")
                break  # Exit the loop if conversation should end
            elif action == "perform_rag_request":
                reply = perform_rag_request(str(inquired_infos), filter_values)
                print("Bot:", reply)
                break  # Exit the loop after performing RAG request
            elif action == "inquire_more_information":
                reply = inquire_more_information(str(inquired_infos))
                print("Bot:", reply)
                message = input("You: ")
                inquired_infos.append("Bot: " + reply)
                inquired_infos.append("User: " + message)
                if message.lower() == 'quit':
                    return  # Exit the chatbot if user decides to quit

        # Log interaction
        c.execute("INSERT INTO logs (user_id, message, response, action) VALUES (?, ?, ?, ?)",
                  (user_id, message, reply, action))
        conn.commit()

def main():
    print("Welcome! Please choose an option:")
    print("1. Register")
    print("2. Login")
    choice = input("Enter choice: ")

    username = input("Username: ")
    password = getpass("Password: ")

    if choice == '1':
        register(username, password)
        user_id = login(username, password)
        if user_id:
            chatbot(user_id)
    elif choice == '2':
        user_id = login(username, password)
        if user_id:
            chatbot(user_id)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
