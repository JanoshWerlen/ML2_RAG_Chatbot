from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
import warnings
warnings.filterwarnings("ignore")
import os
import openai


pdf_paths = ["sample_data/Personalrecht.pdf"]

from dotenv import load_dotenv
# Set your OpenAI API key

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

vector_index = None

for pdf_path in pdf_paths:
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue

    print(f"Processing PDF: {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    pages = loader.load_and_split(text_splitter)

    # Modify this line if you need a different directory for each PDF
    directory = 'index_store'

    # Create a new vector_index or update the existing one
    if vector_index is None:
        vector_index = Chroma.from_documents(pages, OpenAIEmbeddings(), persist_directory=directory)
    else:
        vector_index.add_documents(pages)

    # Persist the final vector_index

    vector_index.persist()

    
    retriever = vector_index.as_retriever(search_type="similarity", search_kwargs={"k":10})
    qa_interface = RetrievalQA.from_chain_type(llm=ChatOpenAI(), chain_type="stuff", retriever=retriever, return_source_documents=True)



def bot_function(question, type):
    
    role = "You are an HR Assistant, You Answer in the language you were asked in. Gib eine Ausführliche Erklärung zu der Frage mit entsprechenden Artikeln."

    if type == "ARG":  
        answer_type = "Arbeitsgesetz"
    else:
        answer_type ="Personalrecht"
    

    result = qa_interface(question)
    print(role+" "+"You only consider Information based on " +answer_type+ " The Question you have to answer is: " +question)
    return result