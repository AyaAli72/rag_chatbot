import faiss
import numpy as np

class FAISSStore:
    def __init__(self, dim):
        self.index = faiss.IndexFlatIP(dim)
        self.texts = []  # store original chunks

    def add_vectors(self, embeddings, texts):
        embeddings = np.array(embeddings, dtype=np.float32)
        self.index.add(embeddings)
        self.texts.extend(texts)

    def search(self, query_vector, top_k=3):
        query_vector = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query_vector, top_k)
        retrieved_texts = []
        for i in indices[0]:
            if i < len(self.texts):
                retrieved_texts.append(self.texts[i])
        return distances, indices, retrieved_texts