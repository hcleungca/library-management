"""Unit tests for the vector embedding generation service."""

import math
from app.services.embedding_service import (
    EMBEDDING_DIM,
    generate_embedding,
    generate_embeddings,
)


def test_embedding_dimension():
    """Verify generated vector has dimension exactly equal to 1536."""
    vec = generate_embedding("Designing Data-Intensive Applications")
    assert isinstance(vec, list)
    assert len(vec) == EMBEDDING_DIM
    assert all(isinstance(v, float) for v in vec)


def test_embedding_normalization():
    """Verify non-empty vector is unit-normalized (L2 norm approx 1.0)."""
    vec = generate_embedding("PostgreSQL and distributed consensus")
    norm = math.sqrt(sum(v * v for v in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-4)


def test_empty_and_whitespace_input():
    """Verify defensive handling for empty and whitespace-only strings returns zero vectors."""
    empty_vec = generate_embedding("")
    assert len(empty_vec) == EMBEDDING_DIM
    assert all(v == 0.0 for v in empty_vec)

    ws_vec = generate_embedding("   \n\t  ")
    assert len(ws_vec) == EMBEDDING_DIM
    assert all(v == 0.0 for v in ws_vec)


def test_embedding_determinism():
    """Verify identical text produces identical embedding vectors."""
    text = "Site Reliability Engineering"
    vec1 = generate_embedding(text)
    vec2 = generate_embedding(text)
    assert vec1 == vec2


def test_batch_generate_embeddings():
    """Verify batch embedding generation produces matching list of vectors."""
    texts = [
        "Distributed Systems and Paxos",
        "Microservices Architecture Patterns",
    ]
    batch = generate_embeddings(texts)
    assert len(batch) == 2
    assert len(batch[0]) == EMBEDDING_DIM
    assert len(batch[1]) == EMBEDDING_DIM
    assert batch[0] == generate_embedding(texts[0])
    assert batch[1] == generate_embedding(texts[1])

