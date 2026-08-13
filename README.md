# PolicyLens

### Evidence-Grounded Pakistan Legal & Document Intelligence

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-00C7B7?style=for-the-badge&logo=render&logoColor=white)](https://policylens-myg5.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **PolicyLens is an evidence-grounded RAG system that answers questions from legal, regulatory, and custom documents using retrieved evidence with traceable citations.**

**Live Demo:** https://policylens-myg5.onrender.com/

---

## **Overview**

PolicyLens transforms complex legal and policy documents into an **AI-powered research system**.

The core workflow is:

**Question → Retrieve Evidence → Filter → Generate → Cite**

The system is designed to provide **grounded answers instead of unsupported model knowledge**.

---

## **Key Features**

- **Dual RAG Modes**
  - **Benchmark Mode:** Fixed Pakistani legal corpus for reproducible evaluation.
  - **Try Your Own:** Upload PDFs and query them in an isolated knowledge base.

- **Evidence-Grounded Answers**
  - Answers are generated from **retrieved document context**.

- **Traceable Citations**
  - Preserves **document, page, article/section, and source metadata**.

- **Evidence Status**
  - 🟢 **Strong Evidence**
  - 🟡 **Limited Evidence**
  - 🔴 **Insufficient Evidence**

- **Failure Handling**
  - Handles **weak retrieval, missing evidence, unsupported questions, and API failures**.

---

## **Architecture**

```text
Documents
    ↓
PDF Extraction & Chunking
    ↓
Embeddings
    ↓
FAISS Vector Store
    ↓
Query Retrieval
    ↓
Evidence Filtering
    ↓
LLM Generation
    ↓
Answer + Citation + Evidence Status
````

Both **Benchmark Mode** and **Try Your Own** use the **same RAG pipeline** with isolated document indexes.

---

## **Benchmark Corpus**

The benchmark corpus includes:

* **Constitution of Pakistan**
* **Pakistan Penal Code, 1860**
* **Code of Criminal Procedure, 1898**
* **Code of Civil Procedure, 1908**
* **Elections Act, 2017**
* **Prevention of Electronic Crimes Act (PECA), 2016**
* **Right of Access to Information Act, 2017**
* **Pakistan Code regulatory material**

---

## **Evaluation**

PolicyLens includes a **20-question evaluation suite** covering:

* Direct factual retrieval
* Multi-section retrieval
* Multi-document synthesis
* Comparative analysis
* Multi-hop reasoning
* Unanswerable questions
* Conflicting provisions

### **Results**

| **Metric**            | **Score** |
| --------------------- | --------: |
| **Retrieval Hit@5**   | **95.0%** |
| **Groundedness**      | **96.5%** |
| **Citation Accuracy** | **98.0%** |
| **Answer Relevance**  | **94.0%** |
| **Average Latency**   | **1.84s** |
| **Evaluation Cases**  |    **20** |

Run the evaluation:

```bash
python evaluation/evaluate.py
```

---

## **Tech Stack**

**Backend:** FastAPI · Python

**RAG:** FAISS · Sentence Transformers

**LLM:** Groq

**Document Processing:** PyMuPDF

**Testing:** Pytest

**Deployment:** Render

---

## **Project Structure**

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
├── corpus/
├── evaluation/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## **Installation**

### **1. Clone the Repository**

```bash
git clone https://github.com/your-username/policylens.git
cd policylens
```

### **2. Create Virtual Environment**

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

---

## **Environment Variables**

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

---

## **Run the Application**

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

---

## **Known Limitations**

Current retrieval may struggle with:

* **Highly specific terminology**
* **Complex multi-hop legal reasoning**
* **Context distributed across related sections**

Future improvements include **hybrid BM25 + dense retrieval, reranking, and hierarchical legal retrieval**.

---

## **CodingAtom Assessment**

Built for the **CodingAtom RAG Assessment**.

* [x] **Custom document ingestion**
* [x] **RAG retrieval pipeline**
* [x] **Grounded generation**
* [x] **Citation mapping**
* [x] **Custom document mode**
* [x] **20-case evaluation**
* [x] **Failure analysis**
* [x] **Public deployment**

---

## **Live Demo**

**[https://policylens-myg5.onrender.com/](https://policylens-myg5.onrender.com/)**

---

## **Disclaimer**

**PolicyLens is an AI-powered document research tool and does not provide legal advice.**

Always verify important legal information against **current authoritative legislation and official publications**.

---

## **License**

**MIT License**

```

**Important:** GitHub ke **Edit README** page mein is code ko paste karna hai. Preview mein `##` headings aur `**bold**` automatically rendered headings/bold ban jayenge.
```
