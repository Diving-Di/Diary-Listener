"""Diary-based memory layer for the AI chat.

The memory has four layers (assembled into a single text block that is injected
into the chat prompt as additional context):

    L1 short-term : current conversation history (handled in routers/chat.py)
    L2 recent     : the most recent diary entries (always relevant)
    L3 related    : diary entries semantically similar to the user's message
                    (local bge embeddings + cosine similarity, computed in app)
    L4 long-term  : an LLM-distilled emotional profile of the user

Everything is scoped by ``user_id`` for privacy isolation, and the whole layer
is gated by the per-user ``allow_ai_diary`` setting (default on).
"""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import embeddings
from .config import get_config
from .models import DiaryEmbedding, DiaryEntry, User, UserMemory, UserSettings

logger = logging.getLogger(__name__)


def entry_text(entry: DiaryEntry) -> str:
    """Combined text used for embedding / retrieval / display.

    Merges the diary content with the vision-generated image caption so that
    image-only entries still carry semantics into the memory layer.
    """
    parts = []
    content = (entry.content or "").strip()
    if content:
        parts.append(content)
    caption = (getattr(entry, "image_caption", "") or "").strip()
    if caption:
        parts.append(f"（配图：{caption}）")
    return " ".join(parts).strip()


def _has_text(entry: DiaryEntry) -> bool:
    return bool(entry_text(entry))


# query filter: entries that have either textual content or an image caption
_HAS_MATERIAL = or_(DiaryEntry.content != "", DiaryEntry.image_caption != "")


# --------------------------------------------------------------------------- #
# settings
# --------------------------------------------------------------------------- #
def get_or_create_settings(db: Session, user: User) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings is None:
        settings = UserSettings(user_id=user.id, allow_ai_diary=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def diary_allowed(db: Session, user: User) -> bool:
    if not get_config()["memory"]["enabled"]:
        return False
    return get_or_create_settings(db, user).allow_ai_diary


# --------------------------------------------------------------------------- #
# indexing (L3 vectors)
# --------------------------------------------------------------------------- #
def index_entry(db: Session, entry: DiaryEntry) -> None:
    """Compute and persist the embedding for a diary entry (best-effort)."""
    text = entry_text(entry)
    if not text:
        return
    vector = embeddings.encode(text)
    if not vector:
        return

    existing = db.query(DiaryEmbedding).filter(DiaryEmbedding.entry_id == entry.id).first()
    if existing:
        existing.vector = embeddings.dumps(vector)
        existing.model = embeddings.model_name()
        existing.dim = len(vector)
    else:
        db.add(
            DiaryEmbedding(
                entry_id=entry.id,
                user_id=entry.user_id,
                model=embeddings.model_name(),
                dim=len(vector),
                vector=embeddings.dumps(vector),
            )
        )
    db.commit()


# --------------------------------------------------------------------------- #
# retrieval
# --------------------------------------------------------------------------- #
def _recent_entries(db: Session, user: User, n: int) -> List[DiaryEntry]:
    if n <= 0:
        return []
    return (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user.id, _HAS_MATERIAL)
        .order_by(DiaryEntry.created_at.desc())
        .limit(n)
        .all()
    )


def _related_entries(db: Session, user: User, query: str, k: int) -> List[DiaryEntry]:
    """Vector retrieval; falls back to keyword LIKE search when no embeddings."""
    if k <= 0 or not query.strip():
        return []

    query_vec = embeddings.encode(query)
    if query_vec:
        rows = (
            db.query(DiaryEmbedding)
            .filter(DiaryEmbedding.user_id == user.id)
            .all()
        )
        if rows:
            import numpy as np  # local import keeps startup light

            q = np.asarray(query_vec, dtype="float32")
            scored = []
            for row in rows:
                vec = embeddings.loads(row.vector)
                if len(vec) != q.shape[0]:
                    continue
                score = float(np.dot(q, np.asarray(vec, dtype="float32")))
                scored.append((score, row.entry_id))
            scored.sort(key=lambda x: x[0], reverse=True)
            top_ids = [eid for _, eid in scored[:k]]
            if top_ids:
                entries = (
                    db.query(DiaryEntry)
                    .filter(DiaryEntry.id.in_(top_ids))
                    .all()
                )
                order = {eid: i for i, eid in enumerate(top_ids)}
                return sorted(entries, key=lambda e: order.get(e.id, 999))

    # Fallback: naive keyword match on the longest token in the query.
    token = max((w for w in query.split()), key=len, default="").strip()
    if len(token) < 2:
        return []
    return (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id == user.id,
            or_(
                DiaryEntry.content.like(f"%{token}%"),
                DiaryEntry.image_caption.like(f"%{token}%"),
            ),
        )
        .order_by(DiaryEntry.created_at.desc())
        .limit(k)
        .all()
    )


def _format_entry(entry: DiaryEntry, max_len: int = 200) -> str:
    date = entry.created_at.strftime("%Y-%m-%d") if entry.created_at else ""
    text = entry_text(entry).replace("\n", " ")
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return f"- {date}：{text}"


def build_diary_context(db: Session, user: User, query: str) -> str:
    """Assemble the diary memory block. Returns '' when disabled / empty."""
    if not diary_allowed(db, user):
        return ""

    cfg = get_config()["memory"]
    sections: List[str] = []

    # L4: long-term emotional profile
    memory = db.query(UserMemory).filter(UserMemory.user_id == user.id).first()
    if memory and memory.summary.strip():
        sections.append("【用户长期情绪画像】\n" + memory.summary.strip())

    # L3 + L2: related and recent diary excerpts (de-duplicated)
    related = _related_entries(db, user, query, cfg["top_k"])
    recent = _recent_entries(db, user, cfg["recent_n"])

    seen = set()
    lines: List[str] = []
    for entry in related + recent:
        if entry.id in seen or not _has_text(entry):
            continue
        seen.add(entry.id)
        lines.append(_format_entry(entry))

    if lines:
        sections.append("【用户日记摘录（按相关度与时间排序）】\n" + "\n".join(lines))

    if not sections:
        return ""

    body = "\n\n".join(sections)
    budget = cfg["char_budget"]
    if len(body) > budget:
        body = body[:budget] + "…"

    return (
        "以下是用户私密日记中提炼出的背景信息，仅供你更好地理解 TA 的心情、经历与情绪。"
        "请在回复中自然地体现关心与共情，不要逐条复述日记，也不要暴露这是系统提供的资料。\n\n"
        + body
    )


# --------------------------------------------------------------------------- #
# L4 profile maintenance
# --------------------------------------------------------------------------- #
def maybe_refresh_profile(db: Session, user: User) -> None:
    """Rebuild the long-term profile every N new diary entries (best-effort)."""
    if not get_config()["memory"]["enabled"]:
        return

    total = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == user.id, _HAS_MATERIAL
    ).count()
    if total == 0:
        return

    memory = db.query(UserMemory).filter(UserMemory.user_id == user.id).first()
    refresh_every = max(1, get_config()["memory"]["profile_refresh_every"])
    if memory and (total - memory.source_count) < refresh_every:
        return

    summary = _generate_profile(db, user)
    if summary is None:
        return

    if memory is None:
        memory = UserMemory(user_id=user.id, summary=summary, source_count=total)
        db.add(memory)
    else:
        memory.summary = summary
        memory.source_count = total
    db.commit()


def _generate_profile(db: Session, user: User) -> Optional[str]:
    """Ask the LLM to distill the user's diary into a short emotional profile."""
    from .ai import summarize  # local import avoids a circular import

    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user.id, _HAS_MATERIAL)
        .order_by(DiaryEntry.created_at.desc())
        .limit(30)
        .all()
    )
    if not entries:
        return None

    diary_text = "\n".join(_format_entry(e, max_len=300) for e in reversed(entries))
    prompt = (
        "下面是某用户最近的日记。请用中文提炼一份简洁的「长期情绪画像」，"
        "150 字以内，涵盖：整体心情趋势、近期重要经历或事件、反复出现的情绪标签、"
        "TA 比较在意的话题。只输出画像正文，不要解释。\n\n" + diary_text
    )
    return summarize(prompt)
