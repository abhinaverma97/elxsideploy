#!/usr/bin/env python3
"""
ISO/IEC Standards PDF Ingestion - Highest Priority for Medical Device Compliance.

Priority Standards:
- ISO 60601-1 (Medical electrical equipment safety)
- ISO 62366-2 (Usability engineering for medical devices)
- ISO 14971 (Risk management for medical devices)

Usage:
  1. Place PDF files in documents/standards/
  2. Run: python scripts/ingest_standards.py
  
The script will:
- Extract text from PDFs (requires pdfplumber or PyPDF2)
- Chunk and tag with highest authority level (5)
- Track versions to avoid re-indexing
- Log what was indexed
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
STANDARDS_DIR = REPO_ROOT / "documents" / "standards"
STANDARDS_DIR.mkdir(parents=True, exist_ok=True)

VERSION_TRACKING_FILE = STANDARDS_DIR / ".indexed_versions.json"

# Try to import PDF library
try:
    import pdfplumber
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_LIBRARY = "pypdf2"
    except ImportError:
        PDF_LIBRARY = None


def read_pdf_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber (preferred)."""
    with pdfplumber.open(pdf_path) as pdf:
        text_parts = []
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)


def read_pdf_with_pypdf2(pdf_path: Path) -> str:
    """Extract text using PyPDF2 (fallback)."""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using available library."""
    if PDF_LIBRARY == "pdfplumber":
        return read_pdf_with_pdfplumber(pdf_path)
    elif PDF_LIBRARY == "pypdf2":
        return read_pdf_with_pypdf2(pdf_path)
    else:
        raise RuntimeError(
            "No PDF library available. Install with:\n"
            "  pip install pdfplumber    (recommended)\n"
            "  or\n"
            "  pip install PyPDF2"
        )


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file to detect changes."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def load_version_tracking() -> Dict:
    """Load tracked file versions."""
    if VERSION_TRACKING_FILE.exists():
        with open(VERSION_TRACKING_FILE, "r") as f:
            return json.load(f)
    return {}


def save_version_tracking(data: Dict):
    """Save tracked file versions."""
    with open(VERSION_TRACKING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Chunk text with larger size for standards documents."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def detect_standard_type(filename: str) -> tuple:
    """
    Detect standard type from filename.
    
    Returns:
        (source_type, standard_name)
    """
    fname_lower = filename.lower()
    
    if "60601" in fname_lower or "iec_60601" in fname_lower:
        return ("iso_60601", "ISO/IEC 60601-1 (Medical Electrical Equipment Safety)")
    elif "62366" in fname_lower or "iso_62366" in fname_lower:
        return ("iso_62366", "ISO 62366-2 (Usability Engineering)")
    elif "14971" in fname_lower or "iso_14971" in fname_lower:
        return ("iso_14971", "ISO 14971 (Risk Management)")
    elif "13485" in fname_lower:
        return ("iso_13485", "ISO 13485 (Quality Management)")
    else:
        return ("iso_standard", "ISO/IEC Standard")


def ingest_standards_pdfs() -> List[Dict]:
    """
    Ingest all PDF files in standards directory.
    
    Returns:
        List of metadata dicts ready for indexing
    """
    print("=" * 60)
    print("ISO/IEC Standards PDF Ingestion")
    print("=" * 60)
    
    if not PDF_LIBRARY:
        print("ERROR: No PDF library installed!")
        print("Install with: pip install pdfplumber")
        return []
    
    pdf_files = list(STANDARDS_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\nNo PDF files found in: {STANDARDS_DIR}")
        print("\nPlease add your ISO standards PDFs:")
        print("  - ISO 60601-1 (Medical electrical equipment)")
        print("  - ISO 62366-2 (Usability engineering)")
        print("  - ISO 14971 (Risk management)")
        print("\nThen re-run this script.")
        return []
    
    print(f"\nFound {len(pdf_files)} PDF files")
    
    versions = load_version_tracking()
    all_metas = []
    
    for pdf_path in pdf_files:
        print(f"\n[Processing] {pdf_path.name}")
        
        # Check if already indexed
        file_hash = compute_file_hash(pdf_path)
        if pdf_path.name in versions and versions[pdf_path.name] == file_hash:
            print(f"  ✓ Already indexed (unchanged)")
            continue
        
        try:
            # Extract text
            print(f"  Extracting text...")
            text = extract_pdf_text(pdf_path)
            
            if not text.strip():
                print(f"  ✗ No text extracted (may be scanned/image PDF)")
                continue
            
            # Detect standard type
            source_type, standard_name = detect_standard_type(pdf_path.name)
            print(f"  Detected: {standard_name}")
            
            # Chunk
            chunks = chunk_text(text, chunk_size=600, overlap=100)
            print(f"  Created {len(chunks)} chunks")
            
            # Create metadata
            for i, chunk_content in enumerate(chunks):
                meta = {
                    "source": str(pdf_path),
                    "chunk": i,
                    "text": chunk_content[:3000],  # Store more text for standards
                    "hash": file_hash,
                    "source_type": source_type,
                    "authority_level": 5  # HIGHEST - ISO standards
                }
                all_metas.append(meta)
            
            # Track version
            versions[pdf_path.name] = file_hash
            print(f"  ✓ Ingested {len(chunks)} chunks")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # Save version tracking
    if all_metas:
        save_version_tracking(versions)
        print(f"\n✓ Total: {len(all_metas)} chunks from {len(pdf_files)} PDFs")
    else:
        print("\n⚠ No new standards to ingest")
    
    return all_metas


def run_ingestion_and_index():
    """Ingest PDFs and add to RAG database."""
    metas = ingest_standards_pdfs()
    
    if not metas:
        return
    
    # Add to database
    print("\nAdding to RAG database...")
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
    except:
        pass
    
    from app.core.retrieval.db import save_many
    
    saved = save_many(metas)
    print(f"✓ Saved {saved} standards chunks to database")
    print("\nDone! ISO standards are now available for RAG retrieval.")


if __name__ == "__main__":
    run_ingestion_and_index()
