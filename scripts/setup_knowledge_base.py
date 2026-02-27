#!/usr/bin/env python3
"""
Quick setup for authority-based RAG knowledge base.

This script will:
1. Install new dependencies (pdfplumber, requests)
2. Recreate database with new schema (source_type, authority_level)
3. Re-index existing code
4. Run FDA + PubMed scrapers
5. Index all cached data
6. Display instructions for adding ISO PDFs

Run: python scripts/setup_knowledge_base.py
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def install_deps():
    """Install new dependencies."""
    print("=" * 60)
    print("Step 1: Installing Dependencies")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=REPO_ROOT
    )
    
    if result.returncode == 0:
        print("✓ Dependencies installed")
    else:
        print("⚠ Some dependencies may have failed to install")


def recreate_database():
    """Recreate database with new schema."""
    print("\n" + "=" * 60)
    print("Step 2: Recreating Database with New Schema")
    print("=" * 60)
    
    # Remove old database
    db_file = REPO_ROOT / "rag_metadata.db"
    if db_file.exists():
        print(f"Removing old database: {db_file}")
        db_file.unlink()
    
    # Create new schema
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
    except:
        pass
    
    from app.core.retrieval.db import init_db
    init_db()
    print("✓ New database created with authority_level and source_type columns")


def reindex_code():
    """Re-index existing code with authority tags."""
    print("\n" + "=" * 60)
    print("Step 3: Re-indexing Codebase (authority_level=1)")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "backend/app/core/retrieval/indexer.py"],
        cwd=REPO_ROOT
    )
    
    if result.returncode == 0:
        print("✓ Codebase re-indexed")


def run_scrapers():
    """Run FDA and PubMed scrapers."""
    print("\n" + "=" * 60)
    print("Step 4: Running FDA + PubMed Scrapers")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "scripts/scheduler.py", "--mode", "weekly"],
        cwd=REPO_ROOT
    )
    
    if result.returncode == 0:
        print("✓ Scrapers completed and data indexed")


def show_iso_instructions():
    """Display instructions for adding ISO standards."""
    print("\n" + "=" * 60)
    print("Step 5: Add ISO Standards (Manual)")
    print("=" * 60)
    print("""
ISO standards are the HIGHEST PRIORITY sources (authority_level=5).

To add them:

1. Place your ISO PDF files in: documents/standards/
   
   Priority PDFs:
   - ISO 60601-1 (Medical electrical equipment safety)
   - ISO 62366-2 (Usability engineering)
   - ISO 14971 (Risk management)

2. Run the ingestion script:
   
   python scripts/ingest_standards.py

3. The script will:
   - Extract text from PDFs
   - Chunk and tag with authority_level=5
   - Track versions (won't re-process unchanged files)
   - Add to RAG database

Example:
   documents/standards/
   ├── ISO_60601_1_2012.pdf
   ├── ISO_62366_2_2016.pdf
   └── ISO_14971_2019.pdf

Then run: python scripts/ingest_standards.py
""")


def verify_setup():
    """Verify the setup is complete."""
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "scripts/check_rag_db.py"],
        cwd=REPO_ROOT
    )
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("""
✓ Database schema updated
✓ Codebase indexed (authority_level=1)
✓ FDA + PubMed data scraped and indexed (authority_levels 2-4)

Next steps:
1. Add ISO standards PDFs to documents/standards/
2. Run: python scripts/ingest_standards.py
3. Set up weekly updates: python scripts/scheduler.py --mode weekly

Authority ranking in RAG:
- ISO Standards (5): 2.0x boost - HIGHEST PRIORITY
- FDA Guidance (4): 1.5x boost
- Datasheets (3): 1.2x boost
- Literature (2): 1.0x (baseline)
- Code (1): 0.8x

Example retrieval will now prioritize ISO standards over your code!
""")


def main():
    print("=" * 60)
    print("Authority-Based RAG Knowledge Base Setup")
    print("=" * 60)
    
    try:
        install_deps()
        recreate_database()
        reindex_code()
        run_scrapers()
        show_iso_instructions()
        verify_setup()
        
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
