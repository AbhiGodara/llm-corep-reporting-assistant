import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from typing import List

@st.cache_resource(show_spinner=False)
def build_vector_store(documents):
    """
    Build and cache FAISS vector store.
    Called only once per session.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return FAISS.from_documents(documents, embeddings)

def retrieve_relevant_context(db, query: str, k: int = 3) -> str:
    """
    Retrieve relevant context from vector store.
    """
    try:
        docs = db.similarity_search(query, k=k)
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Regulatory Text')
            context_parts.append(f"--- Excerpt from {source} ---")
            context_parts.append(doc.page_content.strip())
        
        return "\n\n".join(context_parts)
    
    except Exception as e:
        return f"Error retrieving context: {str(e)}\n\nUsing basic regulatory knowledge."
