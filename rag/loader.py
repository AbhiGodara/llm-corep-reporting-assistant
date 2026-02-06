from langchain_community.document_loaders import TextLoader

def load_documents():
    return TextLoader("data/regulatory_text.txt").load()
