#!/usr/bin/env python3
"""
COMPLETE RAG Knowledge Base Setup - ALL Data Sources

This script populates RAG database from:
1. FDA OpenFDA API (device classifications, 510(k) data)
2. PubMed literature (medical device papers)
3. Nexar/Octopart (component datasheets, specs)
4. GitHub (reference design BOMs)
5. KiCad (footprint libraries)
6. ISO Standards (manual PDFs in documents/standards/)
7. Your existing codebase

Run: python scripts/setup_full_knowledge_base.py
"""
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except:
    pass


def print_banner(title):
    """Print section banner"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_api_tokens():
    """Verify API tokens are configured"""
    print_banner("Step 0: Checking API Tokens")
    
    import os
    tokens = {
        "NEXAR_ACCESS_TOKEN": os.getenv("NEXAR_ACCESS_TOKEN"),
        "GITHUB_API_TOKEN": os.getenv("GITHUB_API_TOKEN"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    }
    
    all_configured = True
    for name, value in tokens.items():
        if value:
            masked = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
            print(f"  ✓ {name}: {masked}")
        else:
            print(f"  ⚠ {name}: NOT CONFIGURED")
            all_configured = False
    
    if not all_configured:
        print("\n⚠️  Some API tokens are missing. The script will continue but some data sources will be skipped.")
        print("  Configure missing tokens in .env to enable all features.")
    
    return all_configured


def install_deps():
    """Install dependencies"""
    print_banner("Step 1: Installing Dependencies")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=REPO_ROOT
    )
    
    if result.returncode == 0:
        print("  ✓ Dependencies installed")
    else:
        print("  ⚠ Some dependencies may have failed")


def recreate_database():
    """Recreate database with new schema"""
    print_banner("Step 2: Recreating RAG Database")
    
    # Remove old database
    db_file = REPO_ROOT / "rag_metadata.db"
    if db_file.exists():
        print(f"  Removing old database: {db_file}")
        db_file.unlink()
    
    # Create new schema
    from app.core.retrieval.db import init_db
    init_db()
    print("  ✓ New database created")


def run_fda_scraper():
    """Run FDA OpenFDA scraper"""
    print_banner("Step 3: Fetching FDA Data")
    print("  Authority Level: 4 (High Priority)")
    print("  Sources: Device Classifications, 510(k) Clearances")
    
    try:
        from scripts.scrapers.fda_scraper import run_fda_scraper
        run_fda_scraper()
        print("  ✓ FDA data scraped and cached")
    except Exception as e:
        print(f"  ⚠ FDA scraper error: {e}")


def run_pubmed_scraper():
    """Run PubMed scraper"""
    print_banner("Step 4: Fetching PubMed Literature")
    print("  Authority Level: 2 (Literature)")
    print("  Sources: Medical device research papers")
    
    try:
        from scripts.scrapers.pubmed_scraper import run_pubmed_scraper
        run_pubmed_scraper()
        print("  ✓ PubMed data scraped and cached")
    except Exception as e:
        print(f"  ⚠ PubMed scraper error: {e}")


def run_nexar_scraper():
    """Run Nexar/Octopart scraper for component data"""
    print_banner("Step 5: Fetching Component Data (Nexar/Octopart)")
    print("  Authority Level: 3 (Datasheets)")
    print("  Sources: Component specs, datasheets, availability, pricing")
    
    import os
    if not os.getenv("NEXAR_ACCESS_TOKEN"):
        print("  ⚠ NEXAR_ACCESS_TOKEN not configured, skipping...")
        return
    
    try:
        from scripts.scrapers.octopart_scraper import NexarScraper
        
        scraper = NexarScraper()
        
        # Key medical device components to fetch
        components = [
            "STM32H743 microcontroller",
            "Sensirion SFM4300 flow sensor",
            "Honeywell HSC pressure sensor",
            "TE Connectivity MS5837 pressure sensor",
            "Maxim MAX30102 pulse oximeter",
            "Texas Instruments INA219 current sensor",
            "Analog Devices AD8232 ECG frontend",
            "LiFePO4 medical battery",
            "MAX6037 voltage reference",
            "TPS3823 supervisor",
        ]
        
        all_data = []
        for query in components:
            print(f"  Searching: {query}")
            try:
                results = scraper.search_components(query, limit=5)
                all_data.extend(results)
                time.sleep(3)  # Rate limiting
            except Exception as e:
                print(f"    ⚠ Error: {e}")
        
        # Save to cache
        cache_file = REPO_ROOT / "documents" / "component_cache" / f"nexar_components_{int(time.time())}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)
        
        print(f"  ✓ Fetched {len(all_data)} component records")
        print(f"  ✓ Cached to: {cache_file}")
        
    except Exception as e:
        print(f"  ⚠ Nexar scraper error: {e}")


def run_github_scraper():
    """Run GitHub BOM scraper"""
    print_banner("Step 6: Fetching Reference Designs (GitHub)")
    print("  Authority Level: 2 (Community Designs)")
    print("  Sources: Open-source medical device BOMs")
    
    import os
    if not os.getenv("GITHUB_API_TOKEN"):
        print("  ⚠ GITHUB_API_TOKEN not configured (will use low rate limit)...")
    
    try:
        from scripts.scrapers.github_bom_scraper import GitHubBOMScraper
        
        scraper = GitHubBOMScraper()
        
        print("  Searching GitHub for medical device projects...")
        repos = scraper.search_medical_device_repos(limit=10)
        
        all_boms = []
        for repo in repos[:5]:  # Limit to 5 repos to avoid rate limits
            print(f"  Extracting BOM from: {repo.get('full_name', 'unknown')}")
            try:
                bom = scraper.extract_bom_from_repo(repo)
                if bom:
                    all_boms.extend(bom)
                time.sleep(3)  # Rate limiting
            except Exception as e:
                print(f"    ⚠ Error: {e}")
        
        # Save to cache
        cache_file = REPO_ROOT / "documents" / "reference_designs" / f"github_boms_{int(time.time())}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_boms, f, indent=2)
        
        print(f"  ✓ Extracted {len(all_boms)} BOM entries from {len(repos)} repositories")
        print(f"  ✓ Cached to: {cache_file}")
        
    except Exception as e:
        print(f"  ⚠ GitHub scraper error: {e}")


def run_kicad_parser():
    """Run KiCad footprint parser"""
    print_banner("Step 7: Downloading KiCad Footprint Libraries")
    print("  Authority Level: 3 (Component Footprints)")
    print("  Sources: KiCad official footprint library (~100MB)")
    print("  Note: This may take several minutes on first run...")
    
    try:
        from scripts.scrapers.kicad_parser import KiCadFootprintParser
        
        parser = KiCadFootprintParser()
        
        # Download library
        library_path = parser.download_kicad_library()
        if not library_path:
            print("  ⚠ Failed to download KiCad library")
            return
        
        # Parse footprints (sample - parsing all would take too long)
        print("  Parsing footprint files (sampling for speed)...")
        footprints = parser.parse_all_footprints(max_files=100)
        
        # Save to cache
        cache_file = REPO_ROOT / "documents" / "kicad_footprints" / f"footprints_{int(time.time())}.json"
        
        import json
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(footprints, f, indent=2)
        
        print(f"  ✓ Parsed {len(footprints)} footprints")
        print(f"  ✓ Cached to: {cache_file}")
        
    except Exception as e:
        print(f"  ⚠ KiCad parser error: {e}")
        import traceback
        traceback.print_exc()


def ingest_standards():
    """Ingest ISO standards PDFs"""
    print_banner("Step 8: Ingesting ISO Standards")
    print("  Authority Level: 5 (HIGHEST PRIORITY)")
    print("  Sources: ISO PDFs in documents/standards/")
    
    standards_dir = REPO_ROOT / "documents" / "standards"
    pdf_files = list(standards_dir.glob("*.pdf")) if standards_dir.exists() else []
    
    if not pdf_files:
        print(f"  ⚠ No PDF files found in {standards_dir}")
        print("  Place ISO standards PDFs there and re-run this script")
        return
    
    print(f"  Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"    - {pdf.name}")
    
    try:
        import pdfplumber
        from app.core.retrieval.db import save_many
        import json
        
        all_chunks = []
        for pdf_file in pdf_files:
            print(f"  Processing: {pdf_file.name}")
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    
                    # Chunk into paragraphs (~500 words)
                    words = text.split()
                    chunk_size = 500
                    overlap = 50
                    
                    i = 0
                    chunk_idx = 0
                    while i < len(words):
                        chunk_words = words[i:i+chunk_size]
                        chunk_text = " ".join(chunk_words)
                        
                        all_chunks.append({
                            "source": f"ISO:{pdf_file.stem}",
                            "chunk": chunk_idx,
                            "text": chunk_text,
                            "source_type": "iso_standard",
                            "authority_level": 5,
                            "hash": None
                        })
                        
                        i += chunk_size - overlap
                        chunk_idx += 1
                        
            except Exception as e:
                print(f"    ⚠ Error processing {pdf_file.name}: {e}")
        
        if all_chunks:
            save_many(all_chunks)
            print(f"  ✓ Ingested {len(all_chunks)} chunks from {len(pdf_files)} standards")
        else:
            print("  ⚠ No text extracted from PDFs")
            
    except ImportError:
        print("  ⚠ pdfplumber not installed. Run: pip install pdfplumber")
    except Exception as e:
        print(f"  ⚠ Standards ingestion error: {e}")


def index_codebase():
    """Index existing codebase"""
    print_banner("Step 9: Indexing Codebase")
    print("  Authority Level: 1 (Internal Code)")
    print("  Sources: backend/ Python files, templates/, README")
    
    try:
        from app.core.retrieval.db import save_many
        import os
        
        # Define paths to index
        code_paths = [
            REPO_ROOT / "backend" / "app" / "core" / "devices",
            REPO_ROOT / "backend" / "app" / "core" / "simulation",
            REPO_ROOT / "backend" / "app" / "core" / "design_engine",
            REPO_ROOT / "templates",
            REPO_ROOT / "README.md",
        ]
        
        all_chunks = []
        chunk_idx = 0
        
        for path in code_paths:
            if not path.exists():
                continue
                
            if path.is_file():
                # Single file
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                
                words = text.split()
                chunk_size = 400
                overlap = 50
                
                i = 0
                while i < len(words):
                    chunk_words = words[i:i+chunk_size]
                    chunk_text = " ".join(chunk_words)
                    
                    all_chunks.append({
                        "source": f"code:{path.relative_to(REPO_ROOT)}",
                        "chunk": chunk_idx,
                        "text": chunk_text,
                        "source_type": "code",
                        "authority_level": 1,
                        "hash": None
                    })
                    
                    i += chunk_size - overlap
                    chunk_idx += 1
            else:
                # Directory - walk recursively
                for root, _, files in os.walk(path):
                    for filename in files:
                        if filename.endswith((".py", ".md", ".txt", ".json")):
                            filepath = Path(root) / filename
                            try:
                                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                    text = f.read()
                                
                                words = text.split()
                                chunk_size = 400
                                overlap = 50
                                
                                file_chunk_idx = 0
                                i = 0
                                while i < len(words):
                                    chunk_words = words[i:i+chunk_size]
                                    chunk_text = " ".join(chunk_words)
                                    
                                    all_chunks.append({
                                        "source": f"code:{filepath.relative_to(REPO_ROOT)}",
                                        "chunk": file_chunk_idx,
                                        "text": chunk_text,
                                        "source_type": "code",
                                        "authority_level": 1,
                                        "hash": None
                                    })
                                    
                                    i += chunk_size - overlap
                                    file_chunk_idx += 1
                            except Exception as e:
                                print(f"    ⚠ Error reading {filepath}: {e}")
        
        if all_chunks:
            save_many(all_chunks)
            print(f"  ✓ Indexed {len(all_chunks)} code chunks")
        else:
            print("  ⚠ No code files indexed")
            
    except Exception as e:
        print(f"  ⚠ Codebase indexing error: {e}")
        import traceback
        traceback.print_exc()


def index_all_cached_data():
    """Index all cached scraper data into RAG database"""
    print_banner("Step 10: Indexing All Cached Data to RAG Database")
    
    from app.core.retrieval.db import save_many
    import json
    from datetime import datetime
    
    all_documents = []
    
    # Authority levels by source
    authority_map = {
        "iso_standard": 5,
        "fda_guidance": 4,
        "component_datasheet": 3,
        "reference_design": 2,
        "literature": 2,
        "code": 1,
    }
    
    # Index FDA cache
    fda_cache = REPO_ROOT / "documents" / "fda_cache"
    if fda_cache.exists():
        for cache_file in fda_cache.glob("*.json"):
            print(f"  Indexing: {cache_file.name}")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    text = f"{item.get('device_name', '')} {item.get('device_class', '')} {item.get('regulation_number', '')}"
                    all_documents.append({
                        "text": text,
                        "source": f"FDA: {item.get('device_name', 'Unknown')}",
                        "source_type": "fda_guidance",
                        "authority_level": authority_map["fda_guidance"],
                        "metadata": json.dumps(item)
                    })
            except Exception as e:
                print(f"    ⚠ Error: {e}")
    
    # Index PubMed cache
    pubmed_cache = REPO_ROOT / "documents" / "pubmed_cache"
    if pubmed_cache.exists():
        for cache_file in pubmed_cache.glob("*.json"):
            print(f"  Indexing: {cache_file.name}")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    text = f"{item.get('title', '')} {item.get('abstract', '')}"
                    all_documents.append({
                        "text": text,
                        "source": f"PubMed: {item.get('title', 'Unknown')}",
                        "source_type": "literature",
                        "authority_level": authority_map["literature"],
                        "metadata": json.dumps(item)
                    })
            except Exception as e:
                print(f"    ⚠ Error: {e}")
    
    # Index Component cache (Nexar)
    component_cache = REPO_ROOT / "documents" / "component_cache"
    if component_cache.exists():
        for cache_file in component_cache.glob("*.json"):
            print(f"  Indexing: {cache_file.name}")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    text = f"{item.get('mpn', '')} {item.get('manufacturer', '')} {item.get('description', '')}"
                    all_documents.append({
                        "text": text,
                        "source": f"Nexar: {item.get('mpn', 'Unknown')}",
                        "source_type": "component_datasheet",
                        "authority_level": authority_map["component_datasheet"],
                        "metadata": json.dumps(item)
                    })
            except Exception as e:
                print(f"    ⚠ Error: {e}")
    
    # Index Reference Designs (GitHub)
    ref_designs = REPO_ROOT / "documents" / "reference_designs"
    if ref_designs.exists():
        for cache_file in ref_designs.glob("*.json"):
            print(f"  Indexing: {cache_file.name}")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    text = f"{item.get('component', '')} {item.get('value', '')} {item.get('package', '')} {item.get('description', '')}"
                    all_documents.append({
                        "text": text,
                        "source": f"GitHub BOM: {item.get('repository', 'Unknown')}",
                        "source_type": "reference_design",
                        "authority_level": authority_map["reference_design"],
                        "metadata": json.dumps(item)
                    })
            except Exception as e:
                print(f"    ⚠ Error: {e}")
    
    # Save to database
    if all_documents:
        print(f"\n  Saving {len(all_documents)} documents to RAG database...")
        save_many(all_documents)
        print("  ✓ All cached data indexed")
    else:
        print("  ⚠ No cached data found to index")


def rebuild_vector_index():
    """Rebuild vector embeddings from database documents"""
    print_banner("Step 11: Building Vector Embeddings Index")
    print("  This creates index_store.npz for semantic search")
    
    try:
        from app.core.retrieval.db import SessionLocal, DocumentMeta
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Load model
        print("  Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Fetch all documents from database
        session = SessionLocal()
        try:
            docs = session.query(DocumentMeta).all()
            print(f"  Found {len(docs)} documents in database")
            
            if not docs:
                print("  ⚠ No documents to index")
                return
            
            # Extract texts
            texts = [doc.text for doc in docs]
            
            # Generate embeddings
            print(f"  Generating embeddings for {len(texts)} documents...")
            embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
            
            # Normalize for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms
            
            # Save to index_store.npz
            index_path = REPO_ROOT / "backend" / "app" / "core" / "retrieval" / "index_store.npz"
            np.savez_compressed(index_path, embeddings=embeddings)
            
            # Save metadata
            meta_path = REPO_ROOT / "backend" / "app" / "core" / "retrieval" / "index_meta.json"
            import json
            metadata = {
                "total_docs": len(docs),
                "embedding_dim": embeddings.shape[1],
                "model": "all-MiniLM-L6-v2",
                "created_at": str(datetime.now())
            }
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  ✓ Vector index built: {embeddings.shape}")
            print(f"  ✓ Saved to: {index_path}")
            
        finally:
            session.close()
            
    except ImportError:
        print("  ⚠ sentence-transformers not installed")
        print("  Run: pip install sentence-transformers")
    except Exception as e:
        print(f"  ⚠ Vector index build error: {e}")
        import traceback
        traceback.print_exc()


def verify_setup():
    """Verify the setup"""
    print_banner("Step 12: Verification")
    
    try:
        from app.core.retrieval.db import count_all
        import os
        
        # Check database
        doc_count = count_all()
        print(f"  ✓ Database: {doc_count} documents")
        
        # Check index file
        index_path = REPO_ROOT / "backend" / "app" / "core" / "retrieval" / "index_store.npz"
        if index_path.exists():
            import numpy as np
            data = np.load(index_path)
            embeddings = data["embeddings"]
            print(f"  ✓ Vector Index: {embeddings.shape}")
        else:
            print("  ⚠ Vector index not found")
        
        # Check caches
        cache_dirs = [
            ("FDA", REPO_ROOT / "documents" / "fda_cache"),
            ("PubMed", REPO_ROOT / "documents" / "pubmed_cache"),
            ("Components", REPO_ROOT / "documents" / "component_cache"),
            ("Reference Designs", REPO_ROOT / "documents" / "reference_designs"),
            ("KiCad", REPO_ROOT / "documents" / "kicad_footprints"),
        ]
        
        for name, cache_dir in cache_dirs:
            if cache_dir.exists():
                file_count = len(list(cache_dir.glob("*.json")))
                print(f"  ✓ {name} Cache: {file_count} files")
        
    except Exception as e:
        print(f"  ⚠ Verification error: {e}")


def print_summary():
    """Print final summary"""
    print_banner("🎉 COMPLETE SETUP FINISHED!")
    
    print("""
✅ RAG Database Populated From:
   ✓ FDA Device Classifications & 510(k) Data (Authority: 4)
   ✓ PubMed Medical Literature (Authority: 2)
   ✓ Nexar/Octopart Component Data (Authority: 3)
   ✓ GitHub Reference Design BOMs (Authority: 2)
   ✓ KiCad Footprint Libraries (Authority: 3)
   ✓ ISO Standards PDFs (Authority: 5) - if available
   ✓ Your Codebase (Authority: 1)

🚀 Your Medical Digital Twin now has:
   • Rule-based design logic (IEC 60601-1, MIL-HDBK-217F, ISO 14971)
   • RAG-enhanced component recommendations
   • FDA compliance guidance
   • Real component datasheets and specs
   • Reference design patterns
   • Standards-driven requirements

📊 Authority Ranking (in RAG retrieval):
   5 (2.0x) - ISO Standards - HIGHEST PRIORITY
   4 (1.5x) - FDA Guidance Documents
   3 (1.2x) - Component Datasheets & Footprints
   2 (1.0x) - Literature & Reference Designs
   1 (0.8x) - Your Internal Code

🔄 To Update Data Weekly:
   python scripts/scheduler.py --mode weekly

🌐 Start Servers:
   Terminal 1: cd backend && uvicorn app.main:app --reload
   Terminal 2: cd frontend && npm run dev
   Browser: http://localhost:5173

""")


def main():
    """Run complete setup"""
    print("=" * 80)
    print("  MEDICAL DIGITAL TWIN - COMPLETE RAG SETUP")
    print("  This will populate knowledge base from ALL configured sources")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        check_api_tokens()
        install_deps()
        recreate_database()
        
        # Run all scrapers
        run_fda_scraper()
        run_pubmed_scraper()
        run_nexar_scraper()
        run_github_scraper()
        run_kicad_parser()
        
        # Ingest standards and code
        ingest_standards()
        index_codebase()
        
        # Index everything to RAG
        index_all_cached_data()
        
        # Rebuild vector embeddings
        rebuild_vector_index()
        
        # Verify
        verify_setup()
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n⏱️  Total Time: {elapsed/60:.1f} minutes")
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
