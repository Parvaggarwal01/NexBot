import os
from pathlib import Path
import warnings
import re
from typing import List, Dict
import langchain
import time

warnings.filterwarnings("ignore")

# Set environment variables to avoid issues
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Fix langchain attributes
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = None

# Rate limiting variables
last_request_time = 0
MIN_REQUEST_INTERVAL = 2  # 2 seconds between requests

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI


class SimpleDocumentRetriever:
    """Simple document retriever using keyword matching instead of embeddings"""
    
    def __init__(self, documents):
        self.documents = documents
    
    def get_relevant_documents(self, query: str, top_k: int = 3) -> List:
        """Find relevant documents using improved keyword matching"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Add synonyms and related terms
        keyword_expansions = {
            'care': ['continuous', 'assessment', 'reduction', 'experience'],
            'attendance': ['waiver', 'participation', 'present'],
            'certification': ['certificate', 'course', 'completion'],
            'policy': ['guideline', 'rule', 'procedure']
        }
        
        # Expand query words with synonyms
        expanded_words = set(query_words)
        for word in query_words:
            if word in keyword_expansions:
                expanded_words.update(keyword_expansions[word])
        
        # Score documents based on keyword overlap
        scored_docs = []
        for doc in self.documents:
            content = doc.page_content.lower()
            source = doc.metadata.get('source', '').lower()
            
            # Count matches in content
            content_matches = sum(1 for word in expanded_words if word in content)
            
            # Count matches in filename (give higher weight)
            filename_matches = sum(2 for word in expanded_words if word in source)
            
            # Special handling for CARE
            if 'care' in query_lower:
                if 'care' in content or 'continuous assessment' in content:
                    content_matches += 5
                if 'care' in source:
                    filename_matches += 10
            
            # Special handling for attendance
            if 'attendance' in query_lower:
                if 'attendance' in content or 'waiver' in content:
                    content_matches += 5
                if 'attendance' in source:
                    filename_matches += 10
            
            total_score = content_matches + filename_matches
            
            if total_score > 0:
                scored_docs.append((doc, total_score))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:top_k]]


def build_retriever():
    """Build simple keyword-based retriever from documents"""
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

    return SimpleDocumentRetriever(chunks)


def get_qa_chain():
    """Create simple QA system without embeddings"""
    retriever = build_retriever()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )

    def qa_function(query):
        """Simple QA function that retrieves context and generates answer with rate limiting"""
        global last_request_time
        
        try:
            # Rate limiting - ensure minimum time between requests
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < MIN_REQUEST_INTERVAL:
                time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
            
            # Retrieve relevant documents using keyword matching
            docs = retriever.get_relevant_documents(query)
            
            if not docs:
                return "I couldn't find any relevant information in the policy documents for your question. Please try rephrasing your question or ask about attendance, CARE guidelines, or certification details."
            
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
                        # Rate limited, wait longer and retry
                        wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                        print(f"Rate limited, waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise api_error
            
        except Exception as e:
            print(f"Error in QA: {e}")
            if "429" in str(e):
                return "I'm currently experiencing high traffic and need to slow down requests. Please wait a moment and try again. The Google API has rate limits to ensure fair usage."
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"
    
    return qa_function