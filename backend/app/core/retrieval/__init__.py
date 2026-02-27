"""Retrieval utilities for RAG prototype.

This module provides a simple local indexer + retriever using
sentence-transformers embeddings and a lightweight numpy-based
cosine-similarity search. It's intentionally dependency-light so
developers can run a prototype without Faiss/Chroma.
"""

from .indexer import Indexer
from .retriever import Retriever

__all__ = ["Indexer", "Retriever"]
