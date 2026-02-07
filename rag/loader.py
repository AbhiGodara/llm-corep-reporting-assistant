import os
from typing import List
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_regulatory_documents(data_dir: str = "data/regulatory") -> List:
    """
    Load all regulatory text files from directory.
    """
    if not os.path.exists(data_dir):
        return TextLoader("data/regulatory_text.txt").load_and_split()
    
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    return text_splitter.split_documents(documents)
