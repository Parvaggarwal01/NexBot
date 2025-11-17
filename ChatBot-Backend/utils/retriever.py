import os
from pathlib import Path
import langchain

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# ✅ Import from correct LangChain modules
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Set verbose and debug to false to avoid compatibility issues
langchain.verbose = False
langchain.debug = False


def build_retriever():
    data_path = Path("data")
    files = list(data_path.glob("*.pdf")) + list(data_path.glob("*.txt")) + list(data_path.glob("*.xlsx"))

    if not files:
        raise ValueError("No policy files found in 'data' folder. Please add some PDF/TXT/XLSX files.")

    documents = []
    for file in files:
        if file.suffix == ".pdf":
            loader = PyPDFLoader(str(file))
        elif file.suffix == ".txt":
            loader = TextLoader(str(file))
        elif file.suffix == ".xlsx":
            loader = UnstructuredExcelLoader(str(file))
        else:
            continue
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"✅ Loaded {len(chunks)} text chunks")

    # Use a more reliable embedding model with timeout handling
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'timeout': 30}
        )
    except Exception as e:
        print(f"⚠️ HuggingFace model loading failed: {e}")
        # Fallback to basic embeddings if HuggingFace fails
        from langchain_community.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(size=384)
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_db")

    return vectordb.as_retriever(search_kwargs={"k": 3})


def get_qa_chain():
    retriever = build_retriever()

    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        verbose=False
    )

    prompt = ChatPromptTemplate.from_template(
        """You are an educational assistant. Use the following context to answer the question clearly and accurately.

        Context:
        {context}

        Question:
        {input}

        Answer:"""
    )

    # ✅ Using LCEL (LangChain Expression Language) approach
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain
