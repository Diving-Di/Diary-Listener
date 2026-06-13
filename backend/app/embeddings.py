"""Local sentence-embedding helper.

Loads a CPU-friendly Chinese embedding model (``BAAI/bge-small-zh-v1.5`` by
default, the same family used by the sibling ``all-in-rag`` project) lazily on
first use via ``sentence-transformers``.

If the model or its dependencies are unavailable the helper degrades
gracefully: ``encode`` returns ``None`` and callers fall back to keyword /
recency based retrieval, so the app keeps working without the model.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import List, Optional

from .config import get_config

logger = logging.getLogger(__name__)

_model = None
_model_failed = False
_lock = threading.Lock()


def model_name() -> str:
    return get_config()["memory"]["embedding_model"]


def _load_model():
    """Lazily load the SentenceTransformer model (thread-safe, cached)."""
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model

    with _lock:
        if _model is not None or _model_failed:
            return _model
        try:
            from sentence_transformers import SentenceTransformer  # heavy import

            logger.info("Loading embedding model: %s", model_name())
            _model = SentenceTransformer(model_name(), device="cpu")
            logger.info("Embedding model ready")
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Embedding model unavailable, falling back: %s", exc)
            _model_failed = True
            _model = None
    return _model


def is_available() -> bool:
    """Whether semantic embeddings can currently be produced."""
    return _load_model() is not None


def warmup(background: bool = True) -> None:
    """Preload the model into memory to avoid first-request latency.

    By default this runs in a daemon thread so server startup is not blocked by
    the (potentially slow) model load / first-time download. Failures are
    swallowed by ``_load_model`` and the app falls back gracefully.
    """
    if not get_config()["memory"]["enabled"]:
        return
    if background:
        threading.Thread(target=_load_model, name="embedding-warmup", daemon=True).start()
    else:
        _load_model()


def encode(text: str) -> Optional[List[float]]:
    """Return a normalized embedding for ``text`` or ``None`` if unavailable."""
    text = (text or "").strip()
    if not text:
        return None
    model = _load_model()
    if model is None:
        return None
    try:
        vec = model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vec]
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.warning("Embedding encode failed: %s", exc)
        return None


def dumps(vector: List[float]) -> str:
    return json.dumps(vector)


def loads(raw: str) -> List[float]:
    try:
        return [float(x) for x in json.loads(raw)]
    except Exception:
        return []
