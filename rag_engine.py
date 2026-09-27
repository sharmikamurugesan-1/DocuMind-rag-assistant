"""
DocuMind — Enterprise RAG (Retrieval-Augmented Generation) Engine
Dual-mode generation (LLM provider adapter + deterministic local extractive synthesis),
strict hallucination guardrails, and verified source citations.
"""

import os
import re
import time
import math
from typing import List, Dict, Any, Optional

class RAGEngine:
    def __init__(self, chunk_size: int = 250, overlap: int = 40, similarity_threshold: float = 0.12):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.similarity_threshold = similarity_threshold
        self.chunks: List[Dict[str, Any]] = []
        self.documents: Dict[str, Dict[str, Any]] = {}

    def add_document(self, text: str, source_name: str = "document.pdf", doc_id: Optional[str] = None) -> int:
        """Splits document into sentence-aware overlapping chunks and indexes them."""
        doc_key = doc_id or source_name
        self.documents[doc_key] = {
            "source_name": source_name,
            "char_count": len(text),
            "word_count": len(text.split()),
            "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Sentence-preserving chunker
        sentences = re.split(r'(?<=[.!?])\s+', text)
        doc_chunks = []
        current_chunk_words: List[str] = []
        page_approx = 1

        for sent in sentences:
            words = sent.split()
            if not words:
                continue

            if len(current_chunk_words) + len(words) > self.chunk_size and current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                doc_chunks.append({
                    "doc_id": doc_key,
                    "source": source_name,
                    "page": page_approx,
                    "text": chunk_text,
                    "word_count": len(current_chunk_words)
                })
                # Overlap tail words
                overlap_words = current_chunk_words[-self.overlap:] if len(current_chunk_words) > self.overlap else current_chunk_words
                current_chunk_words = overlap_words + words
                if len(doc_chunks) % 3 == 0:
                    page_approx += 1
            else:
                current_chunk_words.extend(words)

        if current_chunk_words:
            doc_chunks.append({
                "doc_id": doc_key,
                "source": source_name,
                "page": page_approx,
                "text": " ".join(current_chunk_words),
                "word_count": len(current_chunk_words)
            })

        self.chunks.extend(doc_chunks)
        return len(doc_chunks)

    def _compute_bm25_similarity(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fast BM25 / TF-IDF ranking with term frequency and document frequency weights."""
        if not self.chunks:
            return []

        STOP_WORDS = {
            "the", "is", "at", "which", "on", "a", "an", "and", "or", "for", "with",
            "about", "what", "when", "where", "how", "who", "whom", "this", "that",
            "from", "are", "was", "were", "been", "have", "has", "had", "does", "did",
            "can", "could", "will", "would", "should", "shall", "may", "might", "must",
            "into", "then", "than", "some", "such", "other"
        }
        query_terms = [
            re.sub(r'[^\w]', '', w.lower()) for w in query.split()
            if len(w) > 2 and re.sub(r'[^\w]', '', w.lower()) not in STOP_WORDS
        ]
        if not query_terms:
            return []

        # Document frequency
        df = {}
        for term in query_terms:
            df[term] = sum(1 for c in self.chunks if term in c["text"].lower())

        total_chunks = len(self.chunks)
        scored_chunks = []

        for c in self.chunks:
            text_lower = c["text"].lower()
            text_words = len(text_lower.split())
            score = 0.0

            for term in query_terms:
                if term in text_lower:
                    tf = text_lower.count(term)
                    # IDF with smooth
                    idf = math.log((total_chunks - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                    score += idf * ((tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * (text_words / 200))))

            if score > 0.0:
                chunk_copy = c.copy()
                chunk_copy["score"] = round(score, 3)
                scored_chunks.append(chunk_copy)

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def _extractive_synthesis(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Synthesizes high-fidelity grounded answer directly from relevant sentences."""
        if not retrieved_chunks:
            return f"I could not locate verified information regarding '{question}' in the active document repository."

        q_words = set(w.lower() for w in re.findall(r'\b\w{3,}\b', question))
        relevant_sentences = []

        for c in retrieved_chunks:
            sents = re.split(r'(?<=[.!?])\s+', c["text"])
            for s in sents:
                s_clean = s.strip()
                if not s_clean or len(s_clean.split()) < 4:
                    continue
                s_words = set(w.lower() for w in re.findall(r'\b\w{3,}\b', s_clean))
                overlap = len(q_words.intersection(s_words))
                if overlap > 0:
                    relevant_sentences.append((overlap, c["source"], c["page"], s_clean))

        if not relevant_sentences:
            best_chunk = retrieved_chunks[0]
            return f"According to {best_chunk['source']} (Page {best_chunk['page']}), the agreement outlines: {best_chunk['text'][:280]}..."

        # Sort by relevance overlap
        relevant_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = relevant_sentences[:3]
        
        # Deduplicate
        unique_texts = []
        for _, src, pg, text in top_sentences:
            if not any(text in u for u in unique_texts):
                unique_texts.append(f"{text} (Ref: {src}, p.{pg})")

        return " ".join(unique_texts)

    def query(self, question: str, top_k: int = 3, api_key: Optional[str] = None, provider: str = "local") -> Dict[str, Any]:
        """Queries repository with strict grounding, fallback synthesis, and latency telemetry."""
        start_time = time.time()
        retrieved = self._compute_bm25_similarity(question, top_k=top_k)

        # Hallucination Guardrail: Refuse if similarity is below threshold
        if not retrieved or retrieved[0]["score"] < self.similarity_threshold:
            elapsed = round((time.time() - start_time) * 1000, 2)
            return {
                "question": question,
                "answer": f"The provided documents do not contain sufficient verified information to answer: '{question}'. Please verify that the target document is uploaded.",
                "citations": [],
                "telemetry": {
                    "latency_ms": elapsed,
                    "chunks_retrieved": 0,
                    "top_score": 0.0,
                    "tokens_estimated": 45,
                    "mode": "grounded_refusal"
                }
            }

        # Synthesis: LLM API if key provided, else deterministic local extractor
        mode = "deterministic_local"
        if api_key and provider != "local":
            try:
                # LLM adapter for OpenAI / Gemini
                import requests
                context = "\n\n".join([f"[{c['source']} - Page {c['page']}]: {c['text']}" for c in retrieved])
                prompt = f"Answer the question based STRICTLY on the context below. If not present, state 'Not found'.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
                
                # Default to OpenAI compatible or Gemini
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1
                    },
                    timeout=8
                )
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"].strip()
                    mode = "api_llm_synthesized"
                else:
                    answer = self._extractive_synthesis(question, retrieved)
            except Exception:
                answer = self._extractive_synthesis(question, retrieved)
        else:
            answer = self._extractive_synthesis(question, retrieved)

        citations = [
            {
                "source": c["source"],
                "page": c["page"],
                "score": c["score"],
                "excerpt": c["text"][:180] + ("..." if len(c["text"]) > 180 else "")
            } for c in retrieved
        ]

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        token_est = int(sum(c["word_count"] for c in retrieved) * 1.3) + len(answer.split())

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "telemetry": {
                "latency_ms": elapsed_ms,
                "chunks_retrieved": len(retrieved),
                "top_score": retrieved[0]["score"] if retrieved else 0.0,
                "tokens_estimated": token_est,
                "mode": mode
            }
        }
