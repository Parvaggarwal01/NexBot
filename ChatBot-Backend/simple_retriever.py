import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Set environment variables to avoid issues
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate


def build_retriever():
    """Build retriever from documents in data folder"""
    data_path = Path("data")
    files = list(data_path.glob("*.pdf")) + list(data_path.glob("*.txt"))

    if not files:
        raise ValueError("No policy files found in 'data' folder. Please add some PDF/TXT files.")

    documents = []
    for file in files:
        try:
            if file.suffix == ".pdf":
                loader = PyPDFLoader(str(file))
            elif file.suffix == ".txt":
                loader = TextLoader(str(file))
            else:
                continue
            documents.extend(loader.load())
        except Exception as e:
            print(f"⚠️ Could not load {file.name}: {e}")
            continue

    if not documents:
        raise ValueError("No documents could be loaded successfully.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"✅ Loaded {len(chunks)} text chunks")

    # Use Google embeddings to match the LLM
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Use FAISS instead of Chroma for simplicity
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})


def get_qa_chain():
    """Create simple QA system with Google Gemini"""
    retriever = build_retriever()

    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )

    def qa_function(query):
        """Simple QA function that retrieves context and generates answer"""
        try:
            # Retrieve relevant documents
            docs = retriever.get_relevant_documents(query)
            
            # Combine context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create prompt with context
            prompt = f"""You are an educational assistant. Use the following context to answer the question clearly and accurately.

Context:
{context}

Question: {query}

Answer:"""
            
            # Generate response
            response = llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            print(f"Error in QA: {e}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"
    
    return qa_function