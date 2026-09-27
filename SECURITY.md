# Security Policy: DocuMind-rag-assistant

## 1. Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## 2. Threat Model & Mitigations

### Prompt Injection & Context Escape
- **Delimiter Isolation:** Context chunks are encapsulated in structured boundary tags (`[DOCUMENT: <name> - PAGE: <n>] ... [/DOCUMENT]`) to prevent adversarial prompt injection embedded inside uploaded documents from hijacking system instructions.
- **Strict Grounding Directive:** The system prompt instructs models to operate in strict closed-world assumption: answers MUST be derived exclusively from the provided context; if absent, the model returns a structured non-hallucination refusal.

### API Key & Credential Safety
- **Zero Hardcoded Secrets:** No third-party LLM API keys (OpenAI, Anthropic, Gemini) are ever hardcoded or committed to git.
- **Graceful Deterministic Fallback:** When no API credentials are supplied in environment variables or request headers, the system routes queries through a local extractive synthesis engine with zero 500 errors and zero external telemetry leaks.

### Document Privacy
- **Ephemerality:** Uploaded temporary files are removed immediately after chunking and vector indexing.
- **Memory Boundary Isolation:** Chunks are tagged with distinct `doc_id` namespaces to support multi-tenant document segregation.

## 3. Reporting a Vulnerability
To report a vulnerability or prompt leakage issue, please contact the maintainer at `sharmika.murugesan@gmail.com`. Disclosures are acknowledged within 24 hours.
