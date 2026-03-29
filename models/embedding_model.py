from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def get_embedding(self, text):
        # توليد الـ embedding
        emb = self.model.encode(text, convert_to_tensor=True)

        # L2 normalization لاستخدام cosine similarity
        emb = emb / np.linalg.norm(emb.cpu().numpy())

        # تحويل النوع لـ float32 لتوافق FAISS
        return emb.cpu().numpy().astype(np.float32)