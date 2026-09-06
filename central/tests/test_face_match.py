import pytest
from services.face_match import cosine, best_match


def test_cosine_identical():
    v = [1.0, 0.0, 0.0]
    assert cosine(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal():
    assert abs(cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_best_match_hits_above_threshold():
    query = [1.0, 0.0, 0.0]
    gallery = [
        (1, "alice", [0.99, 0.01, 0.0]),
        (2, "bob", [0.0, 1.0, 0.0]),
    ]
    hit = best_match(query, gallery, threshold=0.5)
    assert hit is not None
    assert hit["person_name"] == "alice"
    assert hit["similarity"] > 0.9


def test_best_match_none_below_threshold():
    query = [1.0, 0.0]
    gallery = [(1, "x", [0.0, 1.0])]
    assert best_match(query, gallery, threshold=0.8) is None


def test_best_match_empty_gallery():
    assert best_match([1.0], [], threshold=0.1) is None
