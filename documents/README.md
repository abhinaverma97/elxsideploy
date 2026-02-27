# Knowledge Base Documents

This directory contains curated authoritative sources for the RAG (Retrieval-Augmented Generation) system.

## Directory Structure

```
documents/
├── standards/              # ISO/IEC standards (HIGHEST PRIORITY)
│   ├── ISO_60601_1.pdf    # Medical electrical equipment safety
│   ├── ISO_62366_2.pdf    # Usability engineering
│   ├── ISO_14971.pdf      # Risk management
│   └── .indexed_versions.json  # Auto-generated version tracking
│
├── fda_cache/              # Auto-generated FDA scraper results
│   ├── fda_classifications_*.json
│   └── fda_510k_*.json
│
└── pubmed_cache/           # Auto-generated PubMed scraper results
    └── pubmed_results_*.json
```

## Authority Levels

The RAG system ranks sources by authority (1-5):

| Level | Source Type | Examples | Boost Factor |
|-------|-------------|----------|--------------|
| **5** | ISO Standards | 60601, 62366, 14971 | 2.0x |
| **4** | FDA Guidance | 510(k), classifications | 1.5x |
| **3** | Datasheets | Component specs (future) | 1.2x |
| **2** | Literature | PubMed articles | 1.0x |
| **1** | Code/Templates | Your repo code | 0.8x |

## How to Add ISO Standards

### Step 1: Obtain PDFs

Place your ISO standard PDFs in `documents/standards/`:

```
documents/standards/
├── ISO_60601_1_2012.pdf
├── ISO_62366_2_2016.pdf
└── ISO_14971_2019.pdf
```

**Naming convention:** Include the standard number in the filename for auto-detection.

### Step 2: Ingest Standards

```powershell
# Install PDF library (if not already installed)
pip install pdfplumber

# Run ingestion
python scripts/ingest_standards.py
```

The script will:
- Extract text from PDFs
- Chunk into 600-word segments
- Tag with authority level 5
- Track versions (won't re-ingest unchanged files)
- Add to RAG database

### Step 3: Verify

```powershell
python scripts/check_rag_db.py
```

You should see increased document count including ISO standards chunks.

## Automated Scraping

### Weekly Update (FDA + PubMed)

```powershell
python scripts/scheduler.py --mode weekly
```

This fetches:
- FDA device classifications
- Recent 510(k) summaries
- PubMed articles on medical device design/safety

### Index Cached Data Only

If you've already run scrapers:

```powershell
python scripts/scheduler.py --mode index-only
```

## Windows Task Scheduler Setup

To automate weekly updates:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly (Sunday 2 AM)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `scripts/scheduler.py --mode weekly`
7. Start in: `D:\Medical-Digital-Twin`

## Retrieval Examples

Once indexed, high-authority sources automatically rank higher:

```python
from app.core.retrieval.retriever import Retriever

retr = Retriever()
hits = retr.retrieve("pressure alarm thresholds", k=5)

for hit in hits:
    print(f"[Authority {hit['authority_level']}] {hit['source_type']}")
    print(f"  Score: {hit['score']:.3f}")
    print(f"  Source: {hit['source']}")
```

Example output:
```
[Authority 5] iso_60601
  Score: 0.892 (boosted from 0.446)
  Source: ISO_60601_1_2012.pdf

[Authority 4] fda_classification
  Score: 0.780 (boosted from 0.520)
  Source: fda_classifications_*.json

[Authority 1] code
  Score: 0.672 (reduced from 0.840)
  Source: backend/app/core/devices/ventilator.py
```

## Notes

- ISO standards are copyrighted; obtain legitimate copies
- FDA/PubMed data is public domain
- Version tracking prevents duplicate indexing
- Cached JSON files can be deleted; scrapers will regenerate
