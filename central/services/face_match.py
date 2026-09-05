"""Face watchlist matching (cosine similarity on embeddings)."""
import math
from typing import List, Optional, Tuple


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


def best_match(
    query: List[float],
    gallery: List[Tuple[int, str, List[float]]],
    threshold: float = 0.45,
) -> Optional[dict]:
    best = None
    best_sim = threshold
    for gid, name, emb in gallery:
        sim = cosine(query, emb)
        if sim >= best_sim:
            best_sim = sim
            best = {"id": gid, "person_name": name, "similarity": round(sim, 4)}
    return best
