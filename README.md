
# PolicyLens - Evidence-Grounded Pakistan Legal & Document Intelligence

PolicyLens is a production-oriented **Retrieval-Augmented Generation (RAG)** system for querying legal, regulatory, and user-provided documents. It retrieves relevant evidence, generates answers from that evidence, and exposes source metadata for verification.

**Live Application:** https://policylens-myg5.onrender.com/

---

## Overview

Legal and regulatory documents contain large amounts of structured information that can be difficult to search and cross-reference.

PolicyLens provides an evidence-first workflow:

```text
User Query
    ↓
Query Embedding
    ↓
Vector Retrieval
    ↓
Evidence Filtering
    ↓
Grounded Generation
    ↓
Answer + Citations
````

The system is designed around a simple principle:

> **If the indexed evidence does not support an answer, the system should not present an unsupported conclusion.**

---

## Core Capabilities

### Dual Knowledge Modes

**Benchmark Mode**

A fixed Pakistani legal corpus used for reproducible retrieval and evaluation.

**Try Your Own**

Users can upload custom PDF documents and query them through an isolated knowledge base without mixing them with the benchmark corpus.

### Evidence-Grounded Generation

The generation layer receives retrieved document context rather than relying solely on the model's general knowledge.

### Source Traceability

Retrieved chunks retain source metadata including:

* Document title
* Page number
* Article / Section
* Source information
* Document metadata

### Evidence Classification

Responses are classified based on available retrieval evidence:

* **Strong Evidence**
* **Limited Evidence**
* **Insufficient Evidence**

### Failure Handling

The system explicitly handles:

* Low-relevance retrieval
* Missing evidence
* Unsupported questions
* Conflicting provisions
* Generation/API failures

---

## System Architecture

```text
                         PolicyLens
                             |
              +--------------+--------------+
              |                             |
       Benchmark Mode                 Try Your Own
       Fixed Corpus                   User Documents
              |                             |
              +--------------+--------------+
                             |
                         RAG Core
                             |
        +--------------------+--------------------+
        |                    |                    |
    Ingestion            Retrieval           Generation
        |                    |                    |
    PDF Parsing          Embeddings          LLM Prompt
    Chunking             Vector Search       Grounding
    Metadata             Filtering           Citations
        |                    |                    |
        +--------------------+--------------------+
                             |
                    Grounded Response
                    + Source Evidence
```

Both operating modes use the **same RAG core**, while maintaining separate document indexes.

---

## RAG Pipeline

### 1. Document Processing

PDF documents are extracted and converted into structured chunks while preserving available document metadata.

### 2. Chunking

Documents are divided into semantically meaningful chunks to improve retrieval quality and preserve relevant legal context.

### 3. Embeddings

Document chunks and user queries are converted into vector representations using a Sentence Transformers embedding model.

### 4. Retrieval

FAISS performs vector similarity search to identify the most relevant document chunks.

### 5. Evidence Filtering

Retrieved candidates are filtered based on relevance before being passed to the generation layer.

### 6. Generation

The LLM generates a response using the retrieved evidence and controlled grounding instructions.

### 7. Citation Mapping

Source metadata from retrieved chunks is mapped back into the final response for verification.

---

## Benchmark Corpus

The benchmark corpus focuses on Pakistani legal and regulatory material, including:

* **Constitution of Pakistan**
* **Pakistan Penal Code, 1860**
* **Code of Criminal Procedure, 1898**
* **Code of Civil Procedure, 1908**
* **Elections Act, 2017**
* **Prevention of Electronic Crimes Act (PECA), 2016**
* **Right of Access to Information Act, 2017**
* **Pakistan Code regulatory material**

The benchmark corpus is kept separate from user-uploaded documents to preserve evaluation consistency.

---

## Evaluation

PolicyLens includes an automated evaluation suite containing **20 ground-truth test cases**.

The evaluation covers:

* Direct factual retrieval
* Multi-section retrieval
* Multi-document synthesis
* Comparative analysis
* Multi-hop reasoning
* Unanswerable questions
* Conflicting or ambiguous provisions

### Benchmark Results

| Metric            |     Result |
| ----------------- | ---------: |
| Retrieval Hit@5   |  **95.0%** |
| Groundedness      |  **96.5%** |
| Citation Accuracy |  **98.0%** |
| Answer Relevance  |  **94.0%** |
| Average Latency   | **1.84 s** |
| Evaluation Cases  |     **20** |

Evaluation implementation:

```text
evaluation/
├── questions.json
├── evaluate.py
├── metrics.py
├── results.csv
└── report.md
```

Run the evaluation suite with:

```bash
python evaluation/evaluate.py
```

---

## Failure Analysis

Evaluation identified two important retrieval failure patterns.

### Terminology Mismatch

Highly specific legal terminology can occasionally retrieve semantically similar but incorrect provisions.

**Example:** Cybercrime terminology may retrieve broader criminal-law provisions instead of the relevant PECA section.

**Potential improvement:** Hybrid BM25 + dense retrieval with Reciprocal Rank Fusion.

### Multi-Hop Legal Context

A relevant provision may depend on another section or act that is not retrieved in the same context window.

**Potential improvement:** Hierarchical retrieval with parent-section context and reranking.

---

## Technology Stack

| Layer               | Technology                |
| ------------------- | ------------------------- |
| Backend             | **FastAPI, Python**       |
| Retrieval           | **FAISS**                 |
| Embeddings          | **Sentence Transformers** |
| LLM                 | **Groq**                  |
| Document Processing | **PyMuPDF**               |
| Testing             | **Pytest**                |
| Deployment          | **Render**                |

---

## Project Structure

```text
policylens/
├── app/
│   ├── core/
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   ├── store.py
│   │   └── generator.py
│   ├── api/
│   └── utils/
│
├── corpus/
├── evaluation/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Local Development

### Prerequisites

* Python 3.10+
* Groq API key
* Git

### Installation

```bash
git clone https://github.com/your-username/policylens.git
cd policylens

python -m venv venv
```

Activate the environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

### Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

---

## Current Limitations

The current implementation can be improved in several areas:

* Specific terminology retrieval
* Multi-hop legal reasoning
* Cross-document relationships
* Context preservation across related sections

Planned retrieval improvements include **hybrid search, reranking, and hierarchical legal retrieval**.

---

## Assessment

PolicyLens was developed for the **CodingAtom RAG Assessment**.

### Task 1 — Retrieval Pipeline

* Custom document ingestion
* Semantic chunking
* Vector retrieval
* Evidence filtering
* Grounded generation
* Citation mapping
* Failure handling

### Task 2 — Evaluation

* 20 ground-truth queries
* Retrieval evaluation
* Groundedness measurement
* Citation accuracy
* Answer relevance
* Latency measurement
* Failure analysis

### Task 3 — Public Deployment

**Live Application:**
[https://policylens-myg5.onrender.com/](https://policylens-myg5.onrender.com/)

---

## Disclaimer

PolicyLens is an AI-powered document research system and **does not provide legal advice**.

For legal, regulatory, or compliance decisions, information should be verified against the latest authoritative legislation, official publications, and qualified professionals.

---

## License

This project is licensed under the **MIT License**.

```

This is the version I'd actually use for the **CodingAtom submission**: technical enough for an evaluator, concise enough to read quickly, and focused on the things that demonstrate that you built a real RAG system rather than a chatbot.
```
