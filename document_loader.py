"""
DocuMind — Multi-Format Document Ingestion Engine
Extracts plain text and page metadata from PDF, TXT, and Markdown documents.
"""

import os
from typing import Dict, Any

class DocumentLoader:
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Loads file content and returns metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target document {file_path} does not exist.")

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        if ext == '.pdf':
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages = []
            for i, p in enumerate(reader.pages):
                text = p.extract_text()
                if text:
                    pages.append(f"--- PAGE {i+1} ---\n{text}")
            content = "\n\n".join(pages)
            total_pages = len(reader.pages)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            total_pages = max(1, len(content.split()) // 350)

        return {
            "filename": filename,
            "content": content,
            "total_pages": total_pages,
            "word_count": len(content.split()),
            "char_count": len(content)
        }
