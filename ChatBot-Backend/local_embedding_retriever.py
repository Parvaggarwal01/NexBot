import os
from pathlib import Path
import warnings
import numpy as np
from typing import List, Dict
import langchain
import time
import pickle

warnings.filterwarnings("ignore")

# Set environment variables to avoid issues
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Fix langchain attributes
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = None

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI

# Try to import sentence transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# Rate limiting variables
last_request_time = 0
MIN_REQUEST_INTERVAL = 2  # 2 seconds between requests


class LocalEmbeddingRetriever:
    """Document retriever using local sentence transformers (free)"""

    def __init__(self, documents, use_embeddings=True):
        self.documents = documents
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self.embeddings_cache_file = "document_embeddings.pkl"

        if self.use_embeddings:
            self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize local embedding model and create document embeddings"""
        try:
            print("🔄 Loading local embedding model (this may take a moment on first run)...")
            # Use a smaller, faster model that works offline
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Check if we have cached embeddings
            if os.path.exists(self.embeddings_cache_file):
                with open(self.embeddings_cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    if len(cached_data['texts']) == len(self.documents):
                        print("📂 Loading cached embeddings...")
                        self.document_texts = cached_data['texts']
                        self.document_embeddings = cached_data['embeddings']
                        return

            # Create new embeddings
            print("🔄 Creating document embeddings...")
            self.document_texts = [doc.page_content for doc in self.documents]
            self.document_embeddings = self.embedding_model.encode(self.document_texts)

            # Cache the embeddings
            with open(self.embeddings_cache_file, 'wb') as f:
                pickle.dump({
                    'texts': self.document_texts,
                    'embeddings': self.document_embeddings
                }, f)

            print("✅ Embeddings created and cached!")

        except Exception as e:
            print(f"⚠️ Failed to initialize embeddings: {e}")
            print("📝 Falling back to keyword matching...")
            self.use_embeddings = False

    def get_relevant_documents(self, query: str, top_k: int = 3) -> List:
        """Find relevant documents using embeddings or fallback to keywords"""
        if self.use_embeddings:
            return self._get_documents_by_embedding(query, top_k)
        else:
            return self._get_documents_by_keywords(query, top_k)

    def _get_documents_by_embedding(self, query: str, top_k: int) -> List:
        """Find documents using semantic similarity (embeddings)"""
        try:
            # Encode the query
            query_embedding = self.embedding_model.encode([query])

            # Calculate cosine similarity
            similarities = np.dot(query_embedding, self.document_embeddings.T).flatten()

            # Get top k most similar documents
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # Filter out very low similarity scores
            relevant_docs = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    relevant_docs.append(self.documents[idx])

            return relevant_docs

        except Exception as e:
            print(f"⚠️ Embedding search failed: {e}, falling back to keywords")
            return self._get_documents_by_keywords(query, top_k)

    def _get_documents_by_keywords(self, query: str, top_k: int) -> List:
        """Fallback keyword-based search (improved version)"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score documents based on keyword overlap
        scored_docs = []
        for doc in self.documents:
            content = doc.page_content.lower()
            source = doc.metadata.get('source', '').lower()

            # Count matches in content
            content_matches = sum(1 for word in query_words if word in content)

            # Count matches in filename (higher weight)
            filename_matches = sum(3 for word in query_words if word in source)

            # Bonus for exact phrase matches
            phrase_bonus = 5 if query_lower in content else 0

            total_score = content_matches + filename_matches + phrase_bonus

            if total_score > 0:
                scored_docs.append((doc, total_score))

        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:top_k]]


def build_retriever():
    """Build retriever with local embeddings (no API needed)"""
    data_path = Path("data")
    files = list(data_path.glob("*.pdf")) + list(data_path.glob("*.txt")) + list(data_path.glob("*.xlsx")) + list(data_path.glob("*.xls"))

    if not files:
        raise ValueError("No policy files found in 'data' folder. Please add some PDF/TXT/XLSX files.")

    documents = []
    for file in files:
        try:
            if file.suffix == ".pdf":
                loader = PyPDFLoader(str(file))
            elif file.suffix == ".txt":
                loader = TextLoader(str(file))
            elif file.suffix in [".xlsx", ".xls"]:
                loader = UnstructuredExcelLoader(str(file))
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

    # Use local embeddings if available, otherwise fallback to keywords
    use_embeddings = EMBEDDINGS_AVAILABLE
    if not use_embeddings:
        print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")
        print("📝 Using keyword-based search as fallback")

    return LocalEmbeddingRetriever(chunks, use_embeddings=use_embeddings)


def get_qa_chain():
    """Create QA system with local embeddings (no API quota issues)"""
    retriever = build_retriever()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        max_tokens=500,      # Limit response length
        timeout=30,          # 30 second timeout
        max_retries=1,       # Reduce retries from default 6 to 1
        request_timeout=20   # Request timeout
    )

    def qa_function(query):
        """QA function with local document retrieval"""
        global last_request_time

        try:
            # Rate limiting for LLM API calls only
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < MIN_REQUEST_INTERVAL:
                time.sleep(MIN_REQUEST_INTERVAL - time_since_last)

            # Retrieve relevant documents (this is now local/free)
            docs = retriever.get_relevant_documents(query)

            if not docs:
                return "I couldn't find any relevant information in the policy documents for your question. Please try rephrasing your question or ask about the topics covered in your uploaded documents."

            # Combine context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])

            # Create prompt with context
            prompt = f"""You are an educational assistant. Use the following context to answer the question clearly and accurately. Base your answer strictly on the provided context.

Context:
{context}

Question: {query}

Answer:"""

            # Update last request time before making the API call
            last_request_time = time.time()

            # Generate response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = llm.invoke(prompt)
                    return response.content
                except Exception as api_error:
                    if "429" in str(api_error) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"Rate limited, waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise api_error

        except Exception as e:
            print(f"Error in QA: {e}")
            if "429" in str(e):
                return "I'm currently experiencing high traffic and need to slow down requests. Please wait a moment and try again."
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"

    return qa_function


def rebuild_embeddings_cache():
    """Function to rebuild embeddings when new documents are added"""
    if os.path.exists("document_embeddings.pkl"):
        os.remove("document_embeddings.pkl")
        print("🗑️ Cleared old embeddings cache")
    print("🔄 Embeddings will be rebuilt on next query")

def force_rebuild_now():
    """Force immediate rebuild of embeddings"""
    rebuild_embeddings_cache()
    # This will trigger a rebuild on next qa_chain call
    return "Embeddings cache cleared. Restart the application to rebuild with all document types."