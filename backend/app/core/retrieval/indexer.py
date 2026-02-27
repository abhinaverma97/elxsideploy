import os
import json
import math
from typing import List, Dict

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

import numpy as np

STORE_PATH = os.path.join(os.path.dirname(__file__), "index_store.npz")
META_PATH = os.path.join(os.path.dirname(__file__), "index_meta.json")


def _read_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".txt", ".md", ".json", ".html"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                if ext == ".json":
                    try:
                        data = json.load(f)
                        # join values heuristically
                        return "\n".join(str(v) for v in data.values())
                    except Exception:
                        return f.read()
                return f.read()
        else:
            return ""
    except Exception:
        return ""


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
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


class Indexer:
    """Simple indexer that builds embeddings for text chunks from files.

    Usage:
      idx = Indexer(model_name="all-MiniLM-L6-v2")
      idx.index_paths([".samples", "templates/devices", "backend/app/core/devices" ])

    It writes `index_store.npz` (embeddings) and `index_meta.json` (metadata).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def _embed(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            # fallback: random vectors (developer should install sentence-transformers)
            return np.random.normal(size=(len(texts), 384)).astype(np.float32)
        return np.array(self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True))

    def index_paths(self, paths: List[str], chunk_size: int = 400, overlap: int = 50):
        docs = []
        metas: List[Dict] = []
        for p in paths:
            if not os.path.exists(p):
                continue
            if os.path.isfile(p):
                text = _read_text_from_file(p)
                chunks = _chunk_text(text, chunk_size, overlap)
                for i, c in enumerate(chunks):
                    docs.append(c)
                    metas.append({"source": p, "chunk": i, "text": c[:2000]})
            else:
                for root, _, files in os.walk(p):
                    for fname in files:
                        fp = os.path.join(root, fname)
                        text = _read_text_from_file(fp)
                        chunks = _chunk_text(text, chunk_size, overlap)
                        for i, c in enumerate(chunks):
                            docs.append(c)
                            metas.append({"source": fp, "chunk": i, "text": c[:2000]})

        if not docs:
            # clear existing if no docs
            if os.path.exists(STORE_PATH):
                os.remove(STORE_PATH)
            return 0

        embeddings = self._embed(docs)
        # normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        # Save embeddings
        np.savez_compressed(STORE_PATH, embeddings=embeddings)

        # Save metadata to DB (Postgres/SQLAlchemy)
        try:
            from . import db as _db
            # add optional hash field
            for m in metas:
                if "hash" not in m:
                    m["hash"] = None
            saved = _db.save_many(metas)
        except Exception:
            # fallback: write metadata to file
            with open(META_PATH, "w", encoding="utf-8") as f:
                json.dump(metas, f, indent=2)
            saved = len(metas)

        return saved


def _default_paths():
    # repo root = four levels up from this file (backend/app/core/retrieval)
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    # Common useful locations in the repo to index
    candidates = [
        os.path.join(base, "templates"),
        os.path.join(base, "backend", "app", "core"),
        os.path.join(base, "frontend"),
        os.path.join(base, "README.md"),
    ]
    return [p for p in candidates if os.path.exists(p)]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build retrieval index for repository text")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--paths", nargs="*", help="Paths to index; defaults to repo templates/core/frontend/README")
    args = parser.parse_args()

    paths = args.paths if args.paths else _default_paths()
    print("Indexing paths:", paths)
    idx = Indexer(model_name=args.model)
    saved = idx.index_paths(paths)
    print(f"Indexed and saved {saved} chunks.")
