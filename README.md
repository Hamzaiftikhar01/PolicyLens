
# PolicyLens — Evidence-Grounded Document Intelligence

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-00C7B7?style=for-the-badge&logo=render&logoColor=white)](https://policylens-myg5.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **PolicyLens is a citation-grounded RAG platform that answers questions from legal and user-provided documents using retrieved evidence instead of unsupported model knowledge.**

🔗 **Live Demo:** https://policylens-myg5.onrender.com/

---

## Overview

PolicyLens transforms complex legal, regulatory, research, and policy documents into a **searchable AI knowledge base**.

**Question → Retrieve Evidence → Generate Answer → Verify Citation**

The system focuses on **grounded answers, source traceability, and safe failure handling**.

---

## Key Features

- **Dual RAG Modes**
  - **Benchmark Mode:** Fixed Pakistani legal corpus for reproducible evaluation.
  - **Try Your Own:** Upload PDFs and query them using an isolated temporary knowledge base.

- **Evidence-Grounded Answers**  
  Answers are generated using **retrieved document context**.

- **Source Citations**  
  Citations preserve **document, page, section/article, and source metadata**.

- **Evidence Status**
  - 🟢 **Strong Evidence**
  - 🟡 **Limited Evidence**
  - 🔴 **Insufficient Evidence**

- **Failure Handling**  
  Handles **weak retrieval, missing evidence, unsupported questions, and API failures**.

- **Evaluation Framework**  
  Includes **20 ground-truth test cases** covering factual retrieval, multi-document synthesis, comparison, multi-hop reasoning, and unanswerable questions.

---

## Architecture

```text
Documents
    ↓
Extraction & Chunking
    ↓
Embeddings
    ↓
FAISS Vector Store
    ↓
Query Retrieval
    ↓
Relevance Filtering
    ↓
LLM Generation
    ↓
Grounded Answer + Citation