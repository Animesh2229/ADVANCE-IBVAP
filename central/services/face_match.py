"""
Face watchlist matching.

DSA:
- Cosine similarity via vectorized NumPy (matrix-vector) when available
- Linear scan O(G*D); for large G use batch matrix multiply
- Optional FAISS index if installed
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

try:
    import numpy as np
    _HAS_NP = True
except Exception:  # pragma: no cover
    _HAS_NP = False

try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except Exception:  # pragma: no cover
    _HAS_FAISS = False


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    if _HAS_NP:
        aa = np.asarray(a, dtype=np.float32)
        bb = np.asarray(b, dtype=np.float32)
        na = np.linalg.norm(aa)
        nb = np.linalg.norm(bb)
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return float(np.dot(aa, bb) / (na * nb))
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
    if not query or not gallery:
        return None

    if _HAS_NP:
        dim = len(query)
        ids, names, rows = [], [], []
        for gid, name, emb in gallery:
            if emb and len(emb) == dim:
                ids.append(gid)
                names.append(name)
                rows.append(emb)
        if not rows:
            return None
        mat = np.asarray(rows, dtype=np.float32)
        q = np.asarray(query, dtype=np.float32)
        mat_n = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
        q_n = q / (np.linalg.norm(q) + 1e-9)
        sims = mat_n @ q_n
        idx = int(np.argmax(sims))
        best_sim = float(sims[idx])
        if best_sim >= threshold:
            return {"id": ids[idx], "person_name": names[idx], "similarity": round(best_sim, 4)}
        return None

    best = None
    best_sim = threshold
    for gid, name, emb in gallery:
        sim = cosine(query, emb)
        if sim >= best_sim:
            best_sim = sim
            best = {"id": gid, "person_name": name, "similarity": round(sim, 4)}
    return best


class FaceIndex:
    """Optional in-memory index for repeated queries (FAISS IP or NumPy)."""

    def __init__(self):
        self.ids: List[int] = []
        self.names: List[str] = []
        self._mat = None
        self._faiss = None

    def build(self, gallery: List[Tuple[int, str, List[float]]]):
        self.ids, self.names = [], []
        rows = []
        for gid, name, emb in gallery:
            if not emb:
                continue
            self.ids.append(gid)
            self.names.append(name)
            rows.append(emb)
        if not rows or not _HAS_NP:
            self._mat = None
            self._faiss = None
            return
        mat = np.asarray(rows, dtype=np.float32)
        mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
        self._mat = mat
        if _HAS_FAISS:
            index = faiss.IndexFlatIP(mat.shape[1])
            index.add(mat)
            self._faiss = index
        else:
            self._faiss = None

    def search(self, query: List[float], threshold: float = 0.45) -> Optional[dict]:
        if not self.ids or not query or not _HAS_NP:
            return None
        q = np.asarray(query, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)
        if self._faiss is not None:
            D, I = self._faiss.search(q.reshape(1, -1), 1)
            sim = float(D[0][0])
            idx = int(I[0][0])
        else:
            sims = self._mat @ q
            idx = int(np.argmax(sims))
            sim = float(sims[idx])
        if sim >= threshold and idx >= 0:
            return {"id": self.ids[idx], "person_name": self.names[idx], "similarity": round(sim, 4)}
        return None
