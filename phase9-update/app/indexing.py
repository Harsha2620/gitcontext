"""Phase 4: turn chunks into embeddings and store/search them in Qdrant."""
import json
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, FieldCondition, Filter, FilterSelector,
                                  MatchAny, PointStruct, VectorParams)
from sentence_transformers import SentenceTransformer

from app.chunking import Chunk
from app.config import (CHUNKS_PATH, COLLECTION, EMBED_DIM, EMBED_MODEL,
                        QDRANT_PATH, QUERY_PREFIX)

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)  # downloads once (~130 MB)
    return _model


_client_obj = None


def _client() -> QdrantClient:
    """One shared connection (local folder, no Docker needed)."""
    global _client_obj
    if _client_obj is None:
        _client_obj = QdrantClient(path=QDRANT_PATH)
    return _client_obj


def close_client() -> None:
    global _client_obj
    if _client_obj is not None:
        _client_obj.close()
        _client_obj = None


def upsert_chunks(chunks: list[Chunk], repo_name: str, batch: int = 64) -> None:
    """Embed chunks and store them (same chunk id = overwritten)."""
    client = _client()
    model = _get_model()
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        vectors = model.encode([c.text for c in part], normalize_embeddings=True)
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL,
                                  f"{c.metadata['path']}:{c.metadata['name']}:{c.metadata['start_line']}")),
                vector=v.tolist(),
                payload={**c.metadata, "repo": repo_name, "text": c.text},
            )
            for c, v in zip(part, vectors)
        ]
        client.upsert(COLLECTION, points)
        print(f"  indexed {min(i + batch, len(chunks))}/{len(chunks)}")


def build_index(chunks: list[Chunk], repo_name: str, batch: int = 64) -> None:
    client = _client()
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
    )
    upsert_chunks(chunks, repo_name, batch)
    dump_chunks()  # save a copy for keyword search


def delete_paths(paths: list[str]) -> None:
    """Remove every chunk that belongs to the given file paths."""
    if paths:
        _client().delete(COLLECTION, points_selector=FilterSelector(
            filter=Filter(must=[FieldCondition(key="path", match=MatchAny(any=paths))])))


def dump_chunks() -> list[dict]:
    """Read every chunk back from Qdrant and save it to data/chunks.json."""
    client = _client()
    chunks, offset = [], None
    while True:
        points, offset = client.scroll(
            COLLECTION, limit=500, offset=offset, with_payload=True, with_vectors=False
        )
        chunks.extend({"id": str(p.id), **p.payload} for p in points)
        if offset is None:
            break
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS_PATH.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return chunks


def search(question: str, k: int = 5) -> list[dict]:
    """Vector (meaning-based) search."""
    client = _client()
    vec = _get_model().encode(QUERY_PREFIX + question, normalize_embeddings=True)
    hits = client.query_points(COLLECTION, query=vec.tolist(), limit=k).points
    results = [{"id": str(h.id), "score": h.score, **h.payload} for h in hits]
    return results
