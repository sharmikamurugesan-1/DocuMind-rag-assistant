# 🧠 DocuMind — AI-Powered Document Q&A (RAG Assistant)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![RAG Ready](https://img.shields.io/badge/RAG-Vector%20Search-purple.svg)]()

> **Impact:** ⚡ Ask questions to any complex PDF in plain English — no reading required.

**DocuMind** is a Retrieval-Augmented Generation (RAG) assistant that allows users to upload PDF contracts, legal briefs, technical specifications, or policy documents and ask natural language questions. It performs semantic chunking, vector retrieval, and outputs direct answers with exact source page citations.

---

## 📌 RAG Architecture

```
[User Document (PDF/Text)]
            │
            ▼
[Text Chunker & Embedding] ──► Overlapping semantic chunking
            │
            ▼
[Vector Retrieval Index]   ──► TF-IDF & FAISS similarity scoring
            │
            ▼
[Synthesis & Citation Engine] ──► Generates cited answers with page numbers
```

---

## ✨ Features

- **Document Ingestion:** Chunks long-form multi-page documents with sliding window overlap.
- **Semantic Vector Retrieval:** Finds the most relevant paragraphs in milliseconds.
- **Precise Page Citations:** Every generated response points back to the exact source document and page number.
- **REST API + Web UI:** Ready-to-deploy FastAPI endpoints with an interactive browser interface.

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/sharmika-murugesan/DocuMind-rag-assistant.git
cd DocuMind-rag-assistant
pip install -r requirements.txt
```

### 2. Run CLI Test
```bash
python app.py
```

### 3. Run FastAPI Web Server
```bash
uvicorn app:app --reload --port 8000
```
Open your browser at `http://localhost:8000` or view API docs at `http://localhost:8000/docs`.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.10+
- **RAG & Search:** FAISS / Scikit-learn Vector Space, PyMuPDF
- **Data Validation:** Pydantic

---

## 📄 License
MIT License. Developed by **Sharmika Murugesan** — Available for freelance AI & LLM projects.
