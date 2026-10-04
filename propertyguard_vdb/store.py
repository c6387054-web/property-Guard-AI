import os
try:
    import chromadb
except ImportError:
    chromadb = None

class PropertyVectorStore:
    def __init__(self, collection_name="property_listings"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        if chromadb:
            try:
                self.client = chromadb.Client()
                self.collection = self.client.get_or_create_collection(name=collection_name)
            except Exception:
                pass

    def search_listings(self, query_text: str, n_results: int = 3):
        if not self.collection:
            return []
        try:
            return self.collection.query(query_texts=[query_text], n_results=n_results)
        except Exception:
            return []

store = PropertyVectorStore()