«PolicyLens is a citation-grounded RAG platform that answers questions from legal and user-provided documents using retrieved evidence instead of unsupported model knowledge.»

🔗 "Live Demo" (https://policylens-myg5.onrender.com/)

---

What is PolicyLens?

PolicyLens turns complex documents into a searchable AI knowledge base.

Question → Retrieve Evidence → Generate Answer → Verify Citation

It is designed for legal, regulatory, research, and policy documents where traceability and grounded answers matter.

---

Key Features

- Dual RAG Modes
  
  - Benchmark Mode: Fixed Pakistani legal corpus for reproducible evaluation.
  - Try Your Own: Upload PDFs and query them in an isolated temporary knowledge base.

- Evidence-Grounded Answers
  Responses are generated from retrieved document context.

- Source Citations
  Answers preserve document, page, section/article, and source metadata.

- Evidence Status
  
  - 🟢 Strong Evidence
  - 🟡 Limited Evidence
  - 🔴 Insufficient Evidence

- Failure Handling
  Detects weak retrieval, missing evidence, unsupported questions, and API failures.

- Built-in Evaluation
  Includes 20 ground-truth questions covering factual retrieval, multi-document queries, comparison, multi-hop reasoning, and unanswerable questions.

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

Both Benchmark Mode and Try Your Own use the same RAG core; only the knowledge-base namespace changes.

---

Benchmark Corpus

The benchmark includes Pakistani legal and regulatory documents such as:

- Constitution of Pakistan
- Pakistan Penal Code
- Code of Criminal Procedure
- Code of Civil Procedure
- Elections Act
- PECA
- Right of Access to Information Act
- Pakistan Code regulatory material

---

Evaluation

Current benchmark results:

Metric| Result
Retrieval Hit@5| 95.0%
Groundedness| 96.5%
Citation Accuracy| 98.0%
Answer Relevance| 94.0%
Avg. Latency| 1.84s
Test Cases| 20

The evaluation suite is available in:

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
├── evaluation/        # Evaluation harness
├── tests/
├── requirements.txt
└── README.md

---

Run Locally

git clone https://github.com/your-username/policylens.git
cd policylens

python -m venv venv
venv\Scripts\activate       # Windows

pip install -r requirements.txt

Create ".env":

GROQ_API_KEY=your_groq_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
CHUNK_SIZE=800
CHUNK_OVERLAP=150

Run:

streamlit run app.py

---

Known Limitations

Current retrieval can struggle with:

- Highly specific terminology
- Multi-hop cross-document reasoning
- Context split across legal subsections

Planned improvements include hybrid BM25 + dense retrieval, reranking, and hierarchical legal chunking.

---

Disclaimer

PolicyLens is a document research tool, not legal advice. Always verify important legal information against current authoritative sources.

---

Assessment

Built for the CodingAtom RAG Assessment.

- [x] Custom RAG pipeline
- [x] Document ingestion
- [x] Retrieval & generation
- [x] Citation grounding
- [x] Custom document upload
- [x] 20-case evaluation
- [x] Failure analysis
- [x] Public deployment

Live: https://policylens-myg5.onrender.com/

---

License

MIT License
