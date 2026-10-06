"""Central settings. Change values here, not all over the code."""
from pathlib import Path

DATA_DIR = Path("data")
REPOS_DIR = DATA_DIR / "repos"          # cloned repositories go here
QDRANT_PATH = str(DATA_DIR / "qdrant")  # local vector database folder
CHUNKS_PATH = DATA_DIR / "chunks.json"  # all chunks, used by keyword (BM25) search
COLLECTION = "gitcontext"

# Free embedding model that runs on your own computer (no API key needed)
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Reranker (cross-encoder). Small and fast on a laptop CPU (~90 MB).
# Upgrade later to "BAAI/bge-reranker-base" for higher quality.
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
