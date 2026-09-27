"""
DocuMind — FastAPI Application & REST API
"""

import os
from typing import Optional
from pydantic import BaseModel
from rag_engine import RAGEngine

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
except ImportError:
    FastAPI = None

app = FastAPI(title="DocuMind RAG Assistant", version="1.0.0") if FastAPI else None
rag = RAGEngine()

# Load default sample document
DEFAULT_DOC = os.path.join(os.path.dirname(__file__), "sample_docs", "sla_agreement.txt")
if os.path.exists(DEFAULT_DOC):
    with open(DEFAULT_DOC, "r", encoding="utf-8") as f:
        rag.add_document(f.read(), "sla_agreement.pdf")

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

if app:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "online", "indexed_chunks": len(rag.documents)}

    @app.post("/query")
    def query_docs(payload: QueryRequest):
        if not payload.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
        return rag.query(payload.question, payload.top_k)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DocuMind — AI Document Q&A</title>
            <style>
                body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #0b0c14; color: #f8fafc; }
                h1 { color: #f87171; }
                .box { background: #151624; border: 1px solid #2e3048; padding: 24px; border-radius: 12px; margin-top: 20px; }
                input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #3b3d5c; background: #08090f; color: white; margin-top: 10px; }
                button { padding: 12px 24px; background: #f87171; border: none; border-radius: 8px; color: white; font-weight: bold; margin-top: 12px; cursor: pointer; }
                #result { margin-top: 20px; white-space: pre-wrap; font-family: monospace; background: #08090f; padding: 16px; border-radius: 8px; border: 1px solid #222538; }
            </style>
        </head>
        <body>
            <h1>🧠 DocuMind — Document Q&A</h1>
            <p>Ask questions across indexed documents in plain English with cited sources.</p>
            <div class="box">
                <label>Enter your question:</label>
                <input id="q" value="What is the penalty for late service delivery?">
                <button onclick="ask()">Ask DocuMind →</button>
                <div id="result">Waiting for query...</div>
            </div>
            <script>
                async function ask() {
                    const q = document.getElementById('q').value;
                    const resBox = document.getElementById('result');
                    resBox.innerText = 'Searching vector index...';
                    const res = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: q })
                    });
                    const data = await res.json();
                    resBox.innerText = JSON.stringify(data, null, 2);
                }
            </script>
        </body>
        </html>
        """

def cli_test():
    print("=" * 60)
    print("🧠 DocuMind — AI Document Q&A Assistant (CLI Mode)")
    print("=" * 60)
    q = "What is the penalty for late service delivery under Clause 4.2?"
    print(f"[*] Querying: '{q}'")
    res = rag.query(q)
    print(f"\n[✓] Answer: {res['answer']}")
    print("\n📚 Citations:")
    for cit in res['citations']:
        print(f"  - Source: {cit['source']} (Page {cit['page']}) -> {cit['excerpt']}")
    print("=" * 60)

if __name__ == "__main__":
    cli_test()
