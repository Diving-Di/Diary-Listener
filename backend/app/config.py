"""Runtime configuration loader.

Configuration precedence (highest to lowest):
1. Existing environment variables (never overwritten)
2. backend/config.json  (gitignored, holds secrets like the AI api key)
3. Built-in defaults

The AI section follows an OpenAI / DeepSeek compatible schema so the project can
talk to DeepSeek (or any OpenAI-compatible endpoint) by only filling config.json.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    file_cfg = _read_json(BASE_DIR / "config.json")

    ai_cfg = file_cfg.get("ai", {}) if isinstance(file_cfg.get("ai"), dict) else {}
    vision_cfg = ai_cfg.get("vision", {}) if isinstance(ai_cfg.get("vision"), dict) else {}
    mem_cfg = file_cfg.get("memory", {}) if isinstance(file_cfg.get("memory"), dict) else {}

    def pick(env_key: str, cfg_value: Any, default: Any) -> Any:
        if os.environ.get(env_key):
            return os.environ[env_key]
        if cfg_value not in (None, ""):
            return cfg_value
        return default

    def pick_int(env_key: str, cfg_value: Any, default: int) -> int:
        try:
            return int(pick(env_key, cfg_value, default))
        except (TypeError, ValueError):
            return default

    def pick_bool(env_key: str, cfg_value: Any, default: bool) -> bool:
        raw = pick(env_key, cfg_value, None)
        if raw is None:
            return default
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "yes", "on")

    config = {
        "secret_key": pick("SECRET_KEY", file_cfg.get("secret_key"), "dev-insecure-change-me"),
        "media_dir": str(BASE_DIR / "media"),
        "database_url": _build_database_url(file_cfg),
        "ai": {
            # DeepSeek compatible defaults
            "api_key": pick("AI_API_KEY", ai_cfg.get("api_key"), ""),
            "base_url": pick("AI_BASE_URL", ai_cfg.get("base_url"), "https://api.deepseek.com/v1"),
            "model": pick("AI_MODEL", ai_cfg.get("model"), "deepseek-chat"),
            "system_prompt": pick(
                "AI_SYSTEM_PROMPT",
                ai_cfg.get("system_prompt"),
                "你是一个温暖、贴心的 AI 助手，用简洁自然的中文与用户多轮对话。",
            ),
            # Optional vision model for turning diary images into Chinese
            # captions (OpenAI-compatible image_url protocol). DeepSeek's
            # official API has no vision endpoint, so this defaults to Qwen-VL
            # on DashScope. Leave api_key empty to disable image captioning.
            "vision": {
                "api_key": pick("AI_VISION_API_KEY", vision_cfg.get("api_key"), ""),
                "base_url": pick(
                    "AI_VISION_BASE_URL",
                    vision_cfg.get("base_url"),
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ),
                "model": pick("AI_VISION_MODEL", vision_cfg.get("model"), "qwen-vl-plus"),
                "prompt": pick(
                    "AI_VISION_PROMPT",
                    vision_cfg.get("prompt"),
                    "请用一句简洁的中文描述这张图片的主要内容、场景与情绪氛围，"
                    "聚焦可能反映用户心情或经历的细节，不要超过60字，直接输出描述。",
                ),
            },
        },
        "memory": {
            # Whether the diary-based memory layer is enabled at all.
            "enabled": pick_bool("MEMORY_ENABLED", mem_cfg.get("enabled"), True),
            # Local sentence-transformers embedding model (CPU friendly, Chinese).
            "embedding_model": pick(
                "MEMORY_EMBEDDING_MODEL", mem_cfg.get("embedding_model"), "BAAI/bge-small-zh-v1.5"
            ),
            # L2: how many most-recent diary entries to always include.
            "recent_n": pick_int("MEMORY_RECENT_N", mem_cfg.get("recent_n"), 5),
            # L3: how many semantically-related diary entries to retrieve.
            "top_k": pick_int("MEMORY_TOP_K", mem_cfg.get("top_k"), 5),
            # Character budget for the assembled diary context.
            "char_budget": pick_int("MEMORY_CHAR_BUDGET", mem_cfg.get("char_budget"), 1800),
            # L4: rebuild the user profile after this many new diary entries.
            "profile_refresh_every": pick_int(
                "MEMORY_PROFILE_REFRESH_EVERY", mem_cfg.get("profile_refresh_every"), 3
            ),
        },
    }
    return config


def _build_database_url(file_cfg: Dict[str, Any]) -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if file_cfg.get("database_url"):
        return str(file_cfg["database_url"])

    # Always use MySQL. Docker sets DB_HOST=db; local dev defaults to 127.0.0.1.
    name = os.environ.get("DB_NAME", "diary_db")
    user = os.environ.get("DB_USER", "user")
    password = os.environ.get("DB_PASSWORD", "password")
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", "3306")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
