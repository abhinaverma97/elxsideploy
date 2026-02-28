import os
from datetime import datetime
from typing import List, Dict

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Use the unified RAG database at project root
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
    DATABASE_URL = f"sqlite:///{os.path.join(project_root, 'rag_metadata.db')}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class DocumentMeta(Base):
    __tablename__ = "rag_documents"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(1024), index=True)
    chunk = Column(Integer, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    doc_hash = Column(String(128), nullable=True)
    source_type = Column(String(64), index=True, default="code")  # iso_standard, fda_guidance, component_datasheet, medical_literature, code
    authority_level = Column(Integer, default=1)  # 1=code, 2=literature, 3=datasheets, 4=fda, 5=iso_standard


def init_db():
    Base.metadata.create_all(bind=engine)


def save_many(metas: List[Dict]) -> int:
    """Save many metadata entries to the DB. Returns number saved."""
    init_db()
    session = SessionLocal()
    count = 0
    try:
        for m in metas:
            dm = DocumentMeta(
                source=m.get("source"),
                chunk=m.get("chunk"),
                text=m.get("text"),
                doc_hash=m.get("hash"),
                source_type=m.get("source_type", "code"),
                authority_level=m.get("authority_level", 1)
            )
            session.add(dm)
            count += 1
        session.commit()
    finally:
        session.close()
    return count


def fetch_by_indices(indices: List[int]) -> List[Dict]:
    """Fetch metadata rows by 0-based index order. Returns list matching indices length where available."""
    init_db()
    session = SessionLocal()
    try:
        # Map rowid order to query order: simple approach - get all and pick by offset
        results = session.query(DocumentMeta).all()
        out = []
        for i in indices:
            if i < 0 or i >= len(results):
                out.append(None)
            else:
                r = results[i]
                out.append({
                    "source": r.source, 
                    "chunk": r.chunk, 
                    "text": r.text,
                    "source_type": r.source_type,
                    "authority_level": r.authority_level
                })
        return out
    finally:
        session.close()


def count_all() -> int:
    """Return total count of documents in database."""
    init_db()
    session = SessionLocal()
    try:
        return session.query(DocumentMeta).count()
    finally:
        session.close()
        session.close()
