# ContractLens - AI Contract Intelligence & Risk Analysis Engine

ContractLens is an enterprise-grade AI contract intelligence application built for the Agentic AI Hackathon '26. It parses PDF contracts into structured clause trees, extracts key field metadata with verified character-offset citations, tracks obligations and deadlines, answers grounded Q&A questions with citation refusal mechanisms, and analyzes contract risks and market anomalies.

---

## 🌟 Key Features

1. **Page-Aware PDF Parsing & Canonical Offsets**:
   - Parses contract PDFs into page-aware text structure and word bounding boxes.
   - Maintains a single immutable canonical text string for exact character-level offsets across all downstream models.

2. **Clause Segmentation & Classification**:
   - Hierarchical clause tree segmentation (parent/child relations) using pattern matching and fallback paragraph models.
   - Classifies clauses into 14+ legal taxonomy categories (`liability`, `termination`, `indemnification`, `governing_law`, etc.).

3. **Key-Field Extraction with Verified Citations**:
   - Extracts 13+ critical contract fields (effective date, renewal terms, liability caps, payment terms, etc.).
   - Enforces **Code-Verified Grounded Citations**: All quotes are verified by Python code (`QuoteVerifier`) directly against the canonical text; LLMs never supply offsets.

4. **Obligation & Deadline Extraction**:
   - Computes active legal obligations, responsible parties, actions, and due dates.
   - Employs deterministic date arithmetic with configurable reference dates.

5. **Grounded Contract Q&A with Citation Verification & Refusal**:
   - Grounded Q&A chat panel with hybrid retrieval (BM25 + synonym expansion + rules router).
   - Refusal mechanism (`"Not found in the contract."`) for unanswerable or missing document topics.
   - Prompt injection & out-of-scope defense (`<UNTRUSTED_DOCUMENT_TEXT>` wrappers).

6. **Risk & Market Anomaly Analysis Engine (Phase 8)**:
   - Evaluates contracts against standard market baseline terms to compute an overall risk score (0–100).
   - Detects uncapped liabilities, short notice periods, automatic renewal lock-ins, broad indemnities, and non-standard governing laws.
   - Provides actionable recommendations and **Highlight in PDF** trigger links.

---

## 🏗 System Architecture

```
[Contract PDF] ──> [PDFParser (PyMuPDF)] ──> [Canonical Text & Page Maps]
                                                      │
                                                      ▼
                                           [Clause Segmenter & Classifier]
                                                      │
                                                      ▼
                 ┌────────────────────────────────────┼────────────────────────────────────┐
                 │                                    │                                    │
                 ▼                                    ▼                                    ▼
       [Field Extractor Agent]           [Obligation Extractor]                 [Risk & Anomaly Analyzer]
                 │                                    │                                    │
                 └────────────────────────────────────┼────────────────────────────────────┘
                                                      │
                                                      ▼
                                       [Code Quote Citation Verifier]
                                                      │
                                                      ▼
                                   [FastAPI REST API & SQLite Database]
                                                      │
                                                      ▼
                                      [React + Tailwind CSS Frontend]
```

---

## 🚀 Quickstart & Installation

### Backend Setup (FastAPI & Python 3.11)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Running Backend Unit Tests

```bash
cd backend
python -m pytest tests
```

### Running Q&A Benchmark Evaluation

```bash
python eval/run_qa_eval.py --replay
```

### Frontend Setup (React & Vite)

```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Endpoints Overview

- `POST /api/v1/contracts` - Upload contract PDF
- `GET /api/v1/contracts/{id}/versions/{version_id}/clauses` - Get clause hierarchy tree
- `GET /api/v1/contracts/{id}/versions/{version_id}/fields` - Get extracted key fields & verified citations
- `GET /api/v1/contracts/{id}/obligations` - Get extracted obligations & calculated deadlines
- `POST /api/v1/qa/ask` - Ask grounded question about contract
- `GET /api/v1/contracts/{id}/risk` - Get risk summary, overall risk score (0-100), and market anomalies

---

## 📄 License

MIT License. Built for Agentic AI Hackathon '26.
