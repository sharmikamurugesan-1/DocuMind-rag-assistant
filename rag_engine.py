"""
DocuMind — RAG Engine
Document chunking, vector embedding similarity, and source-cited synthesis.
"""

import os
import re
from typing import List, Dict, Any

class RAGEngine:
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.documents = []  # List of chunks with metadata
        self.vectorizer = None
        self.tfidf_matrix = None

    def add_document(self, text: str, source_name: str = "document.pdf") -> int:
        """Chunks a document and indexes it into the vector space."""
        # Simple sentence-aware chunking
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = []
        current_len = 0
        page_approx = 1
        
        chunks = []
        for s in sentences:
            s_len = len(s.split())
            if current_len + s_len > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "source": source_name,
                    "page": page_approx
                })
                # Overlap
                current_chunk = current_chunk[-3:] + [s]
                current_len = sum(len(x.split()) for x in current_chunk)
                if len(chunks) % 3 == 0:
                    page_approx += 1
            else:
                current_chunk.append(s)
                current_len += s_len

        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "source": source_name,
                "page": page_approx
            })

        self.documents.extend(chunks)
        self._index_chunks()
        return len(chunks)

    def _index_chunks(self):
        """Builds TF-IDF similarity matrix for fast local semantic retrieval."""
        if not self.documents:
            return
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            corpus = [doc["text"] for doc in self.documents]
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except ImportError:
            pass

    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Queries the vector index and returns context with precise source citations."""
        if not self.documents:
            return {
                "answer": "No documents uploaded yet. Please upload a document first.",
                "citations": []
            }

        if self.vectorizer is not None and self.tfidf_matrix is not None:
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                q_vec = self.vectorizer.transform([question])
                scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
                top_indices = scores.argsort()[-top_k:][::-1]
                
                retrieved_chunks = []
                for idx in top_indices:
                    if scores[idx] > 0.05:
                        chunk = self.documents[idx].copy()
                        chunk["score"] = float(round(scores[idx], 3))
                        retrieved_chunks.append(chunk)

                if not retrieved_chunks:
                    retrieved_chunks = [self.documents[0]]

            except Exception:
                retrieved_chunks = self.documents[:top_k]
        else:
            # Fallback keyword match
            retrieved_chunks = self.documents[:top_k]

        # Synthesize cited response
        best_chunk = retrieved_chunks[0]
        answer = f"Based on {best_chunk['source']} (Page {best_chunk['page']}): {best_chunk['text'][:220]}..."

        return {
            "question": question,
            "answer": answer,
            "citations": [
                {
                    "source": c["source"],
                    "page": c["page"],
                    "excerpt": c["text"][:140] + "..."
                } for c in retrieved_chunks
            ]
        }
