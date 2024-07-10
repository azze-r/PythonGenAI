import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.docstore.document import Document
import fitz  # PyMuPDF
import io

@st.cache(allow_output_mutation=True)
def load_model_and_prepare_qa(pdf_file):
    # Function to extract text from a PDF
    def extract_text_from_pdf(pdf_file):
        # Convert the Streamlit UploadedFile to BytesIO
        pdf_stream = io.BytesIO(pdf_file.read())
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    # Extract text from the uploaded PDF file
    pdf_text = extract_text_from_pdf(pdf_file)

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=200)
    all_splits = text_splitter.split_text(pdf_text)

    # Convert splits to Document objects
    documents = [Document(page_content=split) for split in all_splits]

    # Generate embeddings
    oembed = OllamaEmbeddings(model="nomic-embed-text")

    # Store embeddings in Chroma vectorstore
    vectorstore = Chroma.from_documents(documents=documents, embedding=oembed)

    # Load the language model
    modelChoiced = "gemma2"
    ollama = Ollama(model=modelChoiced)

    # Create the QA chain
    qachain = RetrievalQA.from_chain_type(ollama, retriever=vectorstore.as_retriever())
    
    return qachain

# Streamlit UI components
st.title("Document-based Chatbot with RAG")

# File uploader for the PDF
uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])

if uploaded_file:
    # Load the model and prepare the QA system
    with st.spinner("Loading model and preparing QA system..."):
        qachain = load_model_and_prepare_qa(uploaded_file)

    st.success("Model loaded and QA system ready!")

    # Input box for user questions
    question = st.text_input("Ask a question about the document:")

    if question:
        with st.spinner("Processing your question..."):
            answer = qachain.invoke({"query": question})
        st.write("Answer:", answer)
