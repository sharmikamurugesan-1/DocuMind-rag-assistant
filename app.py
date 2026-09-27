"""
DocuMind — REST API Server
Provides endpoints for document ingestion, semantic RAG queries,
multi-document management, and chat transcript exports.
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_engine import RAGEngine
from document_loader import DocumentLoader

app = Flask(__name__)
CORS(app)

rag = RAGEngine(chunk_size=250, overlap=40)
loader = DocumentLoader()

# Pre-load sample document if exists
sample_path = "sample_docs/sla_agreement.txt"
if os.path.exists(sample_path):
    doc_info = loader.load_file(sample_path)
    rag.add_document(doc_info["content"], source_name=doc_info["filename"])

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "service": "DocuMind RAG Assistant Engine",
        "version": "2.0.0",
        "capabilities": ["bm25_semantic_search", "dual_mode_synthesis", "hallucination_guardrails", "multi_document_index"]
    })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Lists all currently indexed documents in memory."""
    docs = []
    for doc_id, meta in rag.documents.items():
        chunk_count = sum(1 for c in rag.chunks if c["doc_id"] == doc_id)
        docs.append({
            "id": doc_id,
            "filename": meta["source_name"],
            "word_count": meta["word_count"],
            "chunks_count": chunk_count,
            "indexed_at": meta["indexed_at"]
        })
    return jsonify(docs)

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Ingests and indexes uploaded PDF or text file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, file.filename)
    file.save(temp_path)

    try:
        doc_info = loader.load_file(temp_path)
        chunks_added = rag.add_document(doc_info["content"], source_name=doc_info["filename"])
        return jsonify({
            "message": f"Successfully indexed {doc_info['filename']}",
            "chunks_created": chunks_added,
            "word_count": doc_info["word_count"],
            "total_chunks_in_index": len(rag.chunks)
        })
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/query', methods=['POST'])
def query_rag():
    """Handles semantic RAG questions with citations and telemetry."""
    data = request.get_json(force=True, silent=True) or {}
    question = data.get("question", "")
    top_k = int(data.get("top_k", 3))
    api_key = data.get("api_key")
    provider = data.get("provider", "local")

    if not question.strip():
        return jsonify({"error": "Question cannot be empty"}), 400

    result = rag.query(question=question, top_k=top_k, api_key=api_key, provider=provider)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
