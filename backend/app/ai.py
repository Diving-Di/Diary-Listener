"""DeepSeek / OpenAI compatible chat client.

If an api key is configured (via config.json or env), it calls the configured
chat-completions endpoint. Otherwise it falls back to a simple local echo reply
so the app stays runnable without any credentials.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Union

from .config import get_config


def _local_fallback(messages: List[Dict[str, str]]) -> str:
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    return (
        "（本地模拟回复，未配置 AI API Key）\n"
        f"我收到了你的消息：{last_user}\n"
        "在 backend/config.json 中填入 DeepSeek 的 api_key 即可获得真实回复。"
    )


def generate_reply(history: List[Dict[str, str]], diary_context: str = "") -> str:
    """`history` is a list of {role, content} dicts in chronological order.

    `diary_context`, when provided, is injected as an extra system message so the
    AI can draw on the user's diary (mood, experiences, emotions) as memory.
    """
    config = get_config()
    ai = config["ai"]
    api_key = (ai.get("api_key") or "").strip()

    system_prompt = ai.get("system_prompt") or ""
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if diary_context.strip():
        messages.append({"role": "system", "content": diary_context.strip()})
    messages.extend(history)

    if not api_key:
        return _local_fallback(messages)

    try:
        return _chat_completion(messages)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        detail = exc.read().decode("utf-8", errors="ignore")
        return f"（AI 接口调用失败：HTTP {exc.code}）{detail[:200]}"
    except Exception as exc:  # pragma: no cover - network dependent
        return f"（AI 接口调用失败：{exc}）"


def summarize(prompt: str) -> Optional[str]:
    """One-shot helper used to distill a diary into an emotional profile.

    Returns ``None`` when no API key is configured or the call fails, so the
    caller can simply skip updating the profile.
    """
    config = get_config()
    api_key = (config["ai"].get("api_key") or "").strip()
    if not api_key:
        return None
    try:
        return _chat_completion([{"role": "user", "content": prompt}])
    except Exception:  # pragma: no cover - network dependent
        return None


def describe_image(image_path: str) -> Optional[str]:
    """Turn a local diary image into a short Chinese caption via a vision model.

    Uses the OpenAI-compatible ``image_url`` (base64) protocol against the
    configured ``ai.vision`` endpoint (Qwen-VL by default). Returns ``None`` when
    no vision api key is configured or the call fails, so callers degrade
    gracefully and image captioning simply becomes a no-op.
    """
    vision = get_config()["ai"].get("vision", {})
    api_key = (vision.get("api_key") or "").strip()
    if not api_key:
        return None

    try:
        with open(image_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    if not raw:
        return None

    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": vision.get("prompt") or "描述这张图片"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]
    try:
        caption = _chat_completion(messages, ai_section=vision)
        return (caption or "").strip() or None
    except Exception:  # pragma: no cover - network dependent
        return None


def _chat_completion(
    messages: List[Dict[str, Union[str, list]]],
    ai_section: Optional[Dict] = None,
) -> str:
    config = get_config()
    ai = ai_section if ai_section is not None else config["ai"]
    api_key = (ai.get("api_key") or "").strip()
    url = ai["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": ai.get("model", "deepseek-chat"),
        "messages": messages,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]
