import math


class EmbeddingRerankService:
    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        numerator = sum(a * b for a, b in zip(vec_a, vec_b))
        denom_a = math.sqrt(sum(a * a for a in vec_a))
        denom_b = math.sqrt(sum(b * b for b in vec_b))
        if denom_a == 0 or denom_b == 0:
            return -1.0
        return numerator / (denom_a * denom_b)

    def rerank(self, question: str, docs, top_k: int):
        if not docs:
            return []

        embeddings = self.embedding_provider()
        question_vec = embeddings.embed_query(question)
        doc_texts = [doc.page_content for doc in docs]
        doc_vecs = embeddings.embed_documents(doc_texts)

        scored_docs = []
        for doc, vector in zip(docs, doc_vecs):
            score = self._cosine_similarity(question_vec, vector)
            scored_docs.append((score, doc))

        scored_docs.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
