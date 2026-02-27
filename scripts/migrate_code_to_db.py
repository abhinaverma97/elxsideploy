"""Migrate indexed code chunks from index_meta.json to database with authority_level=1"""
import sys
import json
from pathlib import Path

# Load .env BEFORE importing db module
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

# NOW import db after .env loaded
from backend.app.core.retrieval import db

def migrate_code_chunks():
    """Load index_meta.json and save to database with source_type='code', authority_level=1"""
    
    meta_path = REPO_ROOT / "backend" / "app" / "core" / "retrieval" / "index_meta.json"
    
    if not meta_path.exists():
        print(f"❌ No index_meta.json found at {meta_path}")
        print("   Run the indexer first: python -m backend.app.core.retrieval.indexer")
        return
    
    print(f"Loading metadata from: {meta_path}")
    with open(meta_path, "r", encoding="utf-8") as f:
        metas = json.load(f)
    
    print(f"Found {len(metas)} code chunks in index_meta.json")
    
    # Add source_type and authority_level to all chunks
    for m in metas:
        m["source_type"] = "code"
        m["authority_level"] = 1
        if "hash" not in m:
            m["hash"] = None
    
    print(f"Saving {len(metas)} code chunks to database...")
    saved_count = db.save_many(metas)
    
    print(f"✓ Saved {saved_count} code chunks with authority_level=1")
    
    # Verify
    total = db.count_all()
    print(f"✓ Total documents in database: {total}")

if __name__ == "__main__":
    try:
        db.init_db()
        migrate_code_chunks()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
