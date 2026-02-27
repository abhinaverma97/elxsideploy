import os
import json
from typing import List, Dict

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

import numpy as np

STORE_PATH = os.path.join(os.path.dirname(__file__), "index_store.npz")
META_PATH = os.path.join(os.path.dirname(__file__), "index_meta.json")


class Retriever:
    """Lightweight retriever reading the local index store and returning top-k snippets."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def _embed(self, texts: List[str]):
        if self.model is None:
            return np.random.normal(size=(len(texts), 384)).astype(np.float32)
        return np.array(self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True))

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        if not os.path.exists(STORE_PATH) or not os.path.exists(META_PATH):
            return []

        store = np.load(STORE_PATH)
        embeddings = store["embeddings"]
        # Try to load metadata from DB first (Postgres)
        try:
            from . import db as _db
            # We will later map indices to meta rows via _db.fetch_by_indices
            metas = None
        except Exception:
            with open(META_PATH, "r", encoding="utf-8") as f:
                metas = json.load(f)

        q_emb = self._embed([query])
        # normalize
        q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-12)

        # cosine similarity via dot product
        scores = (embeddings @ q_emb.T).squeeze()
        
        # AUTHORITY WEIGHTING: Boost scores based on authority level
        # Authority levels: 1=code, 2=literature, 3=datasheets, 4=fda, 5=iso_standard
        # Boost multipliers: ISO (5) gets 2.0x, FDA (4) gets 1.5x, etc.
        authority_boost = {5: 2.0, 4: 1.5, 3: 1.2, 2: 1.0, 1: 0.8}
        
        # Fetch metadata to get authority levels
        if metas is None:
            try:
                from . import db as _db
                # Get all metadata for authority weighting
                all_metas = _db.fetch_by_indices(list(range(len(scores))))
                # Apply authority boost
                for idx, meta in enumerate(all_metas):
                    if meta and "authority_level" in meta:
                        boost = authority_boost.get(meta["authority_level"], 1.0)
                        scores[idx] *= boost
            except Exception:
                pass  # No DB, no boosting
        
        # top-k indices after boosting
        idxs = list(reversed(scores.argsort()))[:k]
        results = []
        # If DB-backed metadata available, fetch by indices
        if metas is None:
            try:
                from . import db as _db
                metas = _db.fetch_by_indices(list(idxs))
            except Exception:
                metas = []

        for j, i in enumerate(idxs):
            meta = metas[j] if j < len(metas) and metas[j] is not None else {}
            results.append({
                "score": float(scores[i]),
                "source": meta.get("source"),
                "chunk": meta.get("chunk"),
                "text": (meta.get("text") if meta else None),
                "source_type": meta.get("source_type", "unknown"),
                "authority_level": meta.get("authority_level", 1)
            })

        return results
