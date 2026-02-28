# Scripts Directory

## Quick Start - Automated Pipeline

To populate the RAG database with component data, run:

```powershell
python scripts/run_complete_pipeline.py
```

This will execute all scrapers and ingestion in sequence (~30-60 minutes).

## Prerequisites

1. **Get API Keys** (5 minutes):
   - Octopart: https://octopart.com/api/home (10K queries/month free)
   - GitHub: https://github.com/settings/tokens (optional but recommended)

2. **Configure .env**:
   ```bash
   OCTOPART_API_KEY=your_key_here
   GITHUB_API_TOKEN=your_token_here  # optional
   ```

See [`documents/COMPONENT_DATA_GUIDE.md`](../documents/COMPONENT_DATA_GUIDE.md) for detailed instructions.

## Individual Scripts

### Data Scrapers

#### `scrapers/octopart_scraper.py`
- **Purpose**: Fetch component specs from Octopart API
- **Output**: `documents/component_cache/octopart_components.json`
- **Runtime**: ~10-15 minutes
- **Requires**: OCTOPART_API_KEY in .env

```powershell
python scripts/scrapers/octopart_scraper.py
```

#### `scrapers/github_bom_scraper.py`
- **Purpose**: Extract BOMs from open-source medical device projects
- **Output**: `documents/reference_designs/github_boms.json`
- **Runtime**: 5-30 minutes (depending on token)
- **Requires**: GITHUB_API_TOKEN (optional, increases speed)

```powershell
python scripts/scrapers/github_bom_scraper.py
```

#### `scrapers/kicad_parser.py`
- **Purpose**: Parse KiCad footprint libraries for PCB data
- **Output**: `documents/kicad_footprints/kicad_footprints.json`
- **Runtime**: ~10-15 minutes
- **Requires**: Nothing (downloads ~100MB library)

```powershell
python scripts/scrapers/kicad_parser.py
```

### Data Ingestion

#### `ingest_components.py`
- **Purpose**: Load scraped data into RAG vector database
- **Input**: All cached JSON files from scrapers
- **Runtime**: ~10-20 minutes
- **Result**: 6,000-10,000 documents in RAG

```powershell
python scripts/ingest_components.py
```

## Other Scripts

### `ingest_standards.py`
- Ingest ISO/IEC standards from `documents/standards/`
- Already has ISO 14971, 60601-1, 62366-2

### `setup_knowledge_base.py`
- Initialize RAG database
- Schedule automated scrapers (cron/scheduler)

### `check_rag_db.py`
- Verify RAG database contents
- Print statistics and sample queries

## Troubleshooting

### "Octopart API key not found"
Add `OCTOPART_API_KEY=your_key` to `.env` file

### "Rate limit exceeded"
- Octopart: Wait or get paid plan
- GitHub: Add `GITHUB_API_TOKEN` to increase limit from 60/hr to 5000/hr

### "KiCad download timeout"
Check internet connection. Library is ~100MB. Script caches and can retry.

### "No components found in RAG"
Run `python scripts/ingest_components.py` to load scraped data.

## Expected Results

After running complete pipeline:

| Data Type | Count | Authority |
|-----------|-------|-----------|
| Octopart Components | 100-150 | 4 |
| GitHub BOMs | 500-1000 | 3 |
| KiCad Footprints | 5000-8000 | 3 |
| **Total Documents** | **6000-10000** | **3-4 avg** |

## Next Steps

1. Run automated pipeline: `python scripts/run_complete_pipeline.py`
2. Verify data: `python scripts/check_rag_db.py`
3. Test design generation (should return real components, no TBD)
4. Add manual high-value data (see `documents/COMPONENT_DATA_GUIDE.md`)
   - FDA 510(k) PDFs with BOMs
   - Manufacturer application notes
   - Medical-grade certifications

## Architecture

```
scripts/
├── run_complete_pipeline.py  ← Start here (runs everything)
├── scrapers/
│   ├── octopart_scraper.py   ← Components from API
│   ├── github_bom_scraper.py ← Reference BOMs
│   └── kicad_parser.py        ← PCB footprints
└── ingest_components.py       ← Load into RAG database

Output:
documents/
├── component_cache/           ← Octopart JSON
├── reference_designs/         ← GitHub BOMs
└── kicad_footprints/          ← PCB footprints

RAG Database:
backend/app/core/knowledge_base.py
└── rag_metadata.db (SQLite)
    └── chromadb/ (vectors)
```
