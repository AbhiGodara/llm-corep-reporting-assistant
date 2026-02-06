def retrieve_context(db, query, k=4):
    docs = db.similarity_search(query, k=k)
    return "\n".join([d.page_content for d in docs])