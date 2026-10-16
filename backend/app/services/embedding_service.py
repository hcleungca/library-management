"""Vector embedding generation service using FastEmbed.

Provides fast, local embedding generation without external API dependencies.
Produces 1536-dimensional normalized vectors compatible with PostgreSQL
pgvector HNSW index on books.embedding.
"""

import hashlib
import logging
import math
from collections.abc import Sequence

logger = logging.getLogger(__name__)

EMBEDDING_DIM: int = 1536

# Global lazy-loaded FastEmbed model instance
_embedding_model = None
_model_load_attempted = False


def _get_embedding_model():
    """Lazily load the FastEmbed TextEmbedding model on first invocation."""
    global _embedding_model, _model_load_attempted
    if not _model_load_attempted:
        _model_load_attempted = True
        try:
            import os
            import tempfile
            from fastembed import TextEmbedding

            # Auto-detect a guaranteed-writable cache directory for containerized/restricted runtimes
            cache_dir = os.environ.get("FASTEMBED_CACHE_PATH")
            if not cache_dir:
                home_cache = os.path.expanduser("~/.cache/fastembed")
                try:
                    os.makedirs(home_cache, exist_ok=True)
                    test_file = os.path.join(home_cache, ".write_test")
                    with open(test_file, "w") as f:
                        f.write("1")
                    os.remove(test_file)
                    cache_dir = home_cache
                except Exception:
                    cache_dir = os.path.join(tempfile.gettempdir(), "fastembed_cache")
                    os.makedirs(cache_dir, exist_ok=True)

            # Use lightweight bge-small-en-v1.5 model
            _embedding_model = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5",
                cache_dir=cache_dir,
            )
            logger.info("FastEmbed TextEmbedding model initialized successfully (cache_dir=%s).", cache_dir)
        except Exception as exc:
            logger.warning(
                "FastEmbed not available or failed to load (%s); using deterministic fallback generator.",
                exc,
            )
            _embedding_model = None
    return _embedding_model


def _generate_fallback_vector(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a deterministic, normalized vector for offline/test environments.

    Uses SHA-256 hash projections to guarantee deterministic similarity scores
    across test fixtures and offline development without downloading model weights.
    """
    cleaned = text.strip()
    if not cleaned:
        return [0.0] * dim

    # Derive reproducible pseudo-random sequence from text content
    digest = hashlib.sha256(cleaned.lower().encode("utf-8")).digest()
    raw_vals = [
        math.sin((digest[i % len(digest)] + 1) * (i + 1) * 0.17)
        for i in range(dim)
    ]

    # L2-normalize
    norm = math.sqrt(sum(v * v for v in raw_vals))
    if norm > 0.0:
        return [v / norm for v in raw_vals]
    return [0.0] * dim


def generate_embedding(text: str) -> list[float]:
    """Generate a 1536-dimensional normalized embedding vector for the given text.

    - Cleans and defensive-guards against empty or whitespace-only inputs.
    - Utilizes FastEmbed if installed and model weights are accessible.
    - Zero-pads or truncates to match exactly EMBEDDING_DIM (1536).
    - Falls back to deterministic pseudo-embedding in test/offline modes.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return [0.0] * EMBEDDING_DIM

    # Truncate extremely long inputs (~8000 characters) for safety
    if len(cleaned) > 8000:
        cleaned = cleaned[:8000]

    model = _get_embedding_model()
    if model is not None:
        try:
            # fastembed embed returns a generator of numpy ndarrays
            embeddings = list(model.embed([cleaned]))
            if embeddings:
                vec = embeddings[0].tolist()
                # Zero-pad or adjust to match target vector dimension (1536)
                if len(vec) < EMBEDDING_DIM:
                    vec.extend([0.0] * (EMBEDDING_DIM - len(vec)))
                elif len(vec) > EMBEDDING_DIM:
                    vec = vec[:EMBEDDING_DIM]
                return vec
        except Exception as exc:
            logger.warning(
                "FastEmbed embedding failed; falling back to deterministic generator: %s",
                exc,
            )

    return _generate_fallback_vector(cleaned, dim=EMBEDDING_DIM)


def generate_embeddings(texts: Sequence[str]) -> list[list[float]]:
    """Batch-generate 1536-dimensional embeddings for a sequence of texts."""
    return [generate_embedding(t) for t in texts]

