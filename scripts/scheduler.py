#!/usr/bin/env python3
"""
Knowledge Base Update Scheduler - Orchestrates all scrapers and ingestion.

Run this script manually or via Windows Task Scheduler:
  - Daily: FDA MAUDE updates (not implemented yet)
  - Weekly: FDA guidance + PubMed
  - Monthly: Component datasheets (not implemented yet)
  - On-demand: ISO standards (manual PDF placement)

Usage:
  python scripts/scheduler.py --mode [daily|weekly|monthly|all]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except:
    pass


def run_fda_scraper():
    """Run FDA OpenFDA scraper."""
    print("\n" + "=" * 60)
    print("Running FDA Scraper")
    print("=" * 60)
    from scripts.scrapers.fda_scraper import run_fda_scraper
    return run_fda_scraper()


def run_pubmed_scraper():
    """Run PubMed scraper."""
    print("\n" + "=" * 60)
    print("Running PubMed Scraper")
    print("=" * 60)
    from scripts.scrapers.pubmed_scraper import run_pubmed_scraper
    return run_pubmed_scraper()


def ingest_standards():
    """Ingest ISO standards PDFs."""
    print("\n" + "=" * 60)
    print("Ingesting ISO Standards")
    print("=" * 60)
    from scripts.ingest_standards import ingest_standards_pdfs
    return ingest_standards_pdfs()


def index_cached_data():
    """Index all cached scraper data into RAG database."""
    print("\n" + "=" * 60)
    print("Indexing Cached Data to RAG Database")
    print("=" * 60)
    
    from app.core.retrieval.db import save_many
    import json
    
    all_metas = []
    
    # Index FDA cache
    fda_cache_dir = REPO_ROOT / "documents" / "fda_cache"
    if fda_cache_dir.exists():
        for cache_file in fda_cache_dir.glob("*.json"):
            print(f"Loading {cache_file.name}...")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Convert FDA records to chunks
                for item in data:
                    # Combine all text fields
                    text_parts = []
                    for key, value in item.items():
                        if key not in ["source_type", "authority_level"] and value:
                            text_parts.append(f"{key}: {value}")
                    
                    combined_text = "\n".join(text_parts)
                    
                    # Chunk if too long
                    if len(combined_text) > 2000:
                        # Simple chunking
                        chunks = [combined_text[i:i+2000] for i in range(0, len(combined_text), 1800)]
                    else:
                        chunks = [combined_text]
                    
                    for i, chunk in enumerate(chunks):
                        meta = {
                            "source": f"{cache_file.name}#{item.get('device_name', item.get('k_number', 'unknown'))}",
                            "chunk": i,
                            "text": chunk,
                            "source_type": item.get("source_type", "fda_guidance"),
                            "authority_level": item.get("authority_level", 4)
                        }
                        all_metas.append(meta)
                        
            except Exception as e:
                print(f"  Error loading {cache_file.name}: {e}")
    
    # Index PubMed cache
    pubmed_cache_dir = REPO_ROOT / "documents" / "pubmed_cache"
    if pubmed_cache_dir.exists():
        for cache_file in pubmed_cache_dir.glob("*.json"):
            print(f"Loading {cache_file.name}...")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    articles = json.load(f)
                
                for article in articles:
                    text = f"Title: {article.get('title', '')}\n\n"
                    text += f"Authors: {article.get('authors', '')}\n"
                    text += f"Year: {article.get('year', '')}\n\n"
                    text += f"Abstract: {article.get('abstract', '')}"
                    
                    meta = {
                        "source": f"PMID:{article.get('pmid', 'unknown')}",
                        "chunk": 0,
                        "text": text[:3000],
                        "source_type": article.get("source_type", "medical_literature"),
                        "authority_level": article.get("authority_level", 2)
                    }
                    all_metas.append(meta)
                    
            except Exception as e:
                print(f"  Error loading {cache_file.name}: {e}")
    
    # Save to database
    if all_metas:
        print(f"\nSaving {len(all_metas)} chunks to database...")
        saved = save_many(all_metas)
        print(f"✓ Saved {saved} chunks")
    else:
        print("No cached data to index")
    
    return len(all_metas)


def daily_update():
    """Daily scraper run (lightweight)."""
    print("\n" + "=" * 60)
    print(f"Daily Knowledge Base Update - {datetime.now()}")
    print("=" * 60)
    
    # Currently no daily scrapers implemented
    print("(No daily scrapers configured yet)")


def weekly_update():
    """Weekly scraper run (FDA + PubMed)."""
    print("\n" + "=" * 60)
    print(f"Weekly Knowledge Base Update - {datetime.now()}")
    print("=" * 60)
    
    fda_results = run_fda_scraper()
    pubmed_results = run_pubmed_scraper()
    
    # Index cached data
    indexed = index_cached_data()
    
    print(f"\n✓ Weekly update complete: {indexed} total chunks indexed")


def monthly_update():
    """Monthly update (all sources)."""
    print("\n" + "=" * 60)
    print(f"Monthly Knowledge Base Update - {datetime.now()}")
    print("=" * 60)
    
    # Run all scrapers
    run_fda_scraper()
    run_pubmed_scraper()
    
    # Ingest any new standards
    standards = ingest_standards()
    
    # Index all
    indexed = index_cached_data()
    
    print(f"\n✓ Monthly update complete: {indexed + len(standards)} total chunks indexed")


def main():
    parser = argparse.ArgumentParser(description="Knowledge base update scheduler")
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "monthly", "all", "index-only"],
        default="weekly",
        help="Update frequency mode"
    )
    
    args = parser.parse_args()
    
    if args.mode == "daily":
        daily_update()
    elif args.mode == "weekly":
        weekly_update()
    elif args.mode == "monthly":
        monthly_update()
    elif args.mode == "all":
        monthly_update()
    elif args.mode == "index-only":
        index_cached_data()


if __name__ == "__main__":
    main()
