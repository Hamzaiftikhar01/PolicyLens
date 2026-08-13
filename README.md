PolicyLens — Evidence-Grounded Document Intelligence

""Live Demo" (https://img.shields.io/badge/Live%20Demo-Render-00C7B7?style=for-the-badge&logo=render&logoColor=white)" (https://policylens-myg5.onrender.com/)
""Python" (https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)" (https://www.python.org/)
""Streamlit" (https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)" (https://streamlit.io/)
""License" (https://img.shields.io/badge/License-MIT-green.svg)" (LICENSE)

«PolicyLens is a citation-grounded RAG platform that answers questions from legal and user-provided documents using retrieved evidence instead of unsupported model knowledge.»

🔗 Live Demo: https://policylens-myg5.onrender.com/

---

Overview

PolicyLens transforms complex legal, regulatory, research, and policy documents into a searchable AI knowledge base.

Question → Retrieve Evidence → Generate Answer → Verify Citation

The system focuses on grounded answers, source traceability, and safe failure handling.

---

Key Features

- Dual RAG Modes
  
  - Benchmark Mode: Fixed Pakistani legal corpus for reproducible evaluation.
  - Try Your Own: Upload PDFs and query them using an isolated temporary knowledge base.

- Evidence-Grounded Answers
  Answers are generated using retrieved document context.

- Source Citations
  Citations preserve document, page, section/article, and source metadata.

- Evidence Status
  
  - 🟢 Strong Evidence
  - 🟡 Limited Evidence
  - 🔴 Insufficient Evidence

- Failure Handling
  Handles weak retrieval, missing evidence, unsupported questions, and API failures.

- Evaluation Framework
  Includes 20 ground-truth test cases covering factual retrieval, multi-document synthesis, comparison, multi-hop reasoning, and unanswerable questions.

---

Architecture

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

Both Benchmark Mode and Try Your Own use the same RAG core, with isolated knowledge-base namespaces.

---

Benchmark Corpus

The benchmark corpus contains Pakistani legal and regulatory documents including:

- Constitution of Pakistan
- Pakistan Penal Code
- Code of Criminal Procedure
- Code of Civil Procedure
- Elections Act
- Prevention of Electronic Crimes Act (PECA)
- Right of Access to Information Act
- Pakistan Code regulatory material

---

Evaluation

PolicyLens is evaluated using 20 ground-truth questions.

Metric| Result
Retrieval Hit@5| 95.0%
Groundedness| 96.5%
Citation Accuracy| 98.0%
Answer Relevance| 94.0%
Average Latency| 1.84s
Test Cases| 20

Evaluation implementation:

evaluation/
├── questions.json
├── evaluate.py
├── metrics.py
├── results.csv
└── report.md

---

Tech Stack

Python · Streamlit · FAISS · Sentence Transformers · Groq · PyMuPDF · Pytest

---

Project Structure

policylens/
├── app.py
├── app/
│   ├── core/          # RAG pipeline
│   ├── ui/            # Streamlit interface
│   └── utils/
├── corpus/            # Benchmark documents
├── evaluation/        # Evaluation framework
├── tests/
├── requirements.txt
└── README.md

---

Installation

1. Clone

git clone https://github.com/your-username/policylens.git
cd policylens

2. Create Virtual Environment

Windows:

python -m venv venv
venv\Scripts\activate

Linux/macOS:

python -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

---

Environment Variables

Create a ".env" file:

GROQ_API_KEY=your_groq_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
CHUNK_SIZE=800
CHUNK_OVERLAP=150

---

Run the Application

streamlit run app.py

The application will be available at:

http://localhost:8501

---

Run Evaluation

python evaluation/evaluate.py

Run tests:

pytest

---

Known Limitations

Current retrieval may struggle with:

- Highly specific terminology
- Multi-hop cross-document reasoning
- Context split across legal subsections

Potential improvements include hybrid BM25 + dense retrieval, reranking, and hierarchical legal chunking.

---

CodingAtom Assessment

Built for the CodingAtom RAG Assessment.

- [x] Custom RAG pipeline
- [x] Document ingestion
- [x] Vector retrieval
- [x] Grounded generation
- [x] Citation system
- [x] Custom document upload
- [x] 20-case evaluation
- [x] Failure analysis
- [x] Public deployment

---

Live Demo

https://policylens-myg5.onrender.com/

---

Disclaimer

PolicyLens is a document research tool and does not provide legal advice.

For important legal decisions, always verify information against current authoritative sources and official publications.

---

License

MIT License
