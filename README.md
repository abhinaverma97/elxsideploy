# DigitalTwin For Medical Devices

**Digital Twin** is a professional, deterministic medical device system design and compliance tool. It allows engineers to transition seamlessly from structured requirements to validated system architectures and digital twin simulations, ending with one-click code generation for embedded targets.

## 🚀 Key Features

- **Multi-Device Support**: Optimized for Class I (Pulse Oximeter), Class II (Ventilator), and Class III (Hemodialysis) medical devices.
- **Authority-Based RAG System**: Intelligent knowledge base with 1900+ documents prioritizing ISO 60601-1 (electrical safety), ISO 62366-2 (usability), FDA guidance, and peer-reviewed medical literature over code templates.
- **Deterministic Design Graph**: Automatically infers subsystem architectures and interfaces from engineering requirements grounded in regulatory standards.
- **Hierarchical Visualization**: Generates High-Level (HLD) and Logical signal-flow diagrams using Graphviz.
- **Multi-Fidelity Digital Twins**: Supports L1 (Static), L2 (Dynamic), and L3 (Physics-based) simulation models for behavior validation.
- **Safety & Compliance**: Integrated ISO 14971 risk assessment, fault injection testing, automated compliance traceability with citations to authoritative sources.
- **Automated Scrapers**: Weekly updates from FDA OpenFDA API (device classifications, 510k summaries) and PubMed (medical literature).
- **One-Click Codegen**: Generates a standard, runnable Python repository structure based on the validated design.

---

## 🛠️ Local Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Graphviz**: Required for diagram rendering.
  - **Windows**: [Download and Install](https://graphviz.org/download/) (Ensure you add it to the system **PATH** during installation).
- **GROQ API Key**: Required for LLM-powered requirements analysis and design generation.
  - Sign up at [console.groq.com](https://console.groq.com)
  - Create a `.env` file in the project root with your API key

### 1. Backend Setup
1.  Navigate to the project root.
2.  Create a virtual environment:
    ```powershell
    python -m venv venv
    ```
3.  Activate the environment:
    ```powershell
    # Windows
    .\venv\Scripts\Activate.ps1
    # Linux/Mac
    source venv/bin/activate
    ```
4.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```
5.  Configure environment variables (create `.env` file):
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    DATABASE_URL=sqlite:///D:\Medical-Digital-Twin\rag_metadata.db
    ```
6.  **[One-Time] Initialize RAG Knowledge Base**:
    ```powershell
    python scripts/setup_knowledge_base.py
    ```
    This automated script will:
    - Install required dependencies (pdfplumber, requests)
    - Create SQLite database with authority-level schema
    - Index your codebase (authority_level=1)
    - Scrape FDA device classifications and 510(k) data (authority_level=4)
    - Scrape PubMed medical literature (authority_level=2)
    - Display instructions for adding ISO standards PDFs
    
7.  **[Optional] Add ISO Standards** (Highest Priority - authority_level=5):
    - Obtain legitimate copies of ISO 60601-1, ISO 62366-2, ISO 14971 PDFs
    - Place them in `documents/standards/`
    - Run: `python scripts/ingest_standards.py`
    - These will receive a **2.0x retrieval boost** in RAG queries

8.  Start the FastAPI server:
    - **NEW**: Requirements are automatically analyzed using RAG-grounded LLM, referencing ISO standards and FDA guidance.
3.  **Build Design**: Go to **Design Graph** and click **"Build Design Graph"** to generate the block diagrams.
4.  **Generate Design Details**: 
    - Click **"Generate Design Details"** to create comprehensive specifications.
    - **NEW**: Design generation queries the knowledge base for ISO 60601-1 electrical safety, ISO 62366-2 usability, and FDA regulatory requirements.
    - Generated designs cite authoritative sources with relevance scores.
5.  **Simulate**: Use the **Digital Twin** tab to run simulations. You can inject faults to test safety mitigations.
6.  **Export & Codegen**: In the **Traceability** tab:
    - Review the Compliance Matrix with ISO/FDA citations.
    - Click **"Generate Code Repository"** to create a structured codebase in `generated_repos/`.

---

## 🧠 RAG Knowledge Base

The system uses an **authority-weighted retrieval-augmented generation (RAG)** architecture to ground all LLM outputs in regulatory standards and peer-reviewed sources.

### Authority Ranking (Retrieval Boost)

| Level | Source Type | Boost | Examples |
|-------|-------------|-------|----------|
| 5 | ISO Standards | **2.0x** | ISO 60601-1 (electrical safety), ISO 62366-2 (usability), ISO 14971 (risk) |
| 4 | FDA Guidance | 1.5x | Device classifications, 510(k) summaries |
| 3 | Component Datasheets | 1.2x | Sensor specs, MCU datasheets |
| 2 | Medical Literature | 1.0x | PubMed articles, clinical studies |
| 1 | Code Templates | 0.8x | Internal codebase examples |

### Knowledge Base Contents (1955 documents)

- **143 ISO Standard Chunks** (60601-1, 62366-2) - Electrical safety, usability engineering
- **183 FDA Device Records** - Classifications, regulatory requirements
- **125 PubMed Articles** - Medical device design research, safety studies
- **1504 Code Templates** - Internal device implementations

### Automated Updates

Weekly scraper updates FDA and PubMed data:
```powershell
python scripts/scheduler.py --mode weekly
```

Set up Windows Task Scheduler for automated runs (see `documents/README.md` for details).

---

## ⚙️ Project Structure

- `backend/`: FastAPI application, core logic, and device models.
  - `app/core/retrieval/`: RAG indexer, retriever, and database schema.
  - `app/core/requirements/`: NLP analyzer with RAG grounding.
  - `app/api/design.py`: Design generation with ISO/FDA context injection.
- `frontend/`: React + Vite + Tailwind CSS application.
- `scripts/`: Database setup, scrapers, schedulers, ISO ingestion.
  - `scrapers/`: FDA OpenFDA and PubMed scrapers.
  - `scheduler.py`: Automated knowledge base updates.
  - `ingest_standards.py`: ISO PDF text extraction and indexing.
- `documents/`: Knowledge base directory structure.
  - `standards/`: ISO PDF files (user-provided).
  - `fda_cache/`: Cached FDA API responses.
  - `pubmed_cache/`: Cached PubMed search results.
  - `README.md`: Complete knowledge base documentation.
- `.samples/`: Pre-configured requirement sets for medical devices.
- `generated_repos/`: Output directory for the automated code generator.
- `rag_metadata.db`: SQLite database with 1955 indexed documents
3.  Start the development server:
    ```powershell
    npm run dev
    ```
    *The application will be available at `http://localhost:5173`.*

---

## 📖 How to Use

1.  **Select Device**: Use the header dropdown to choose between Ventilator, Pulse Oximeter, or Hemodialysis.
2.  **Add Requirements**: 
    - Use the **Requirements** tab to manually add engineering specs.
    - Or click **"Autofill Sample"** to load pre-configured industrial requirements.
3.  **Build Design**: Go to **Design Graph** and click **"Build Design Graph"** to generate the block diagrams.
4.  **Simulate**: Use the **Digital Twin** tab to run simulations. You can inject faults to test safety mitigations.
5.  **Export & Codegen**: In the **Traceability** tab:
    - Review the Compliance Matrix.
    - Click **"Generate Code Repository"** to create a structured codebase in `generated_repos/`.

---

## ⚙️ Project Structure

- `backend/`: FastAPI application, core logic, and device models.
- `frontend/`: React + Vite + Tailwind CSS application.
- `.samples/`: Pre-configured requirement sets for medical devices.
- `generated_repos/`: Output directory for the automated code generator.

---

© 2026 VitaBlueprint Engine — Industry-Grade System Engineering
