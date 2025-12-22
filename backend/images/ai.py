import base64
import json
import os
import urllib.request
import urllib.error
from typing import List, Optional

from config.runtime_config import load_runtime_config


# Ensure env vars can be loaded from config/app_config.json or .env
load_runtime_config()

MAX_TAGS = 8
MAX_TAG_LEN = 20


def _safe_read_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, 'rb') as f:
            return f.read()
    except Exception:
        return None





def _qwen_vision_tags(image_path: str) -> List[str]:
    api_key = os.environ.get('AI_VISION_API_KEY')
    if not api_key:
        raise RuntimeError('AI_VISION_API_KEY not set')

    # Default to DashScope OpenAI-compatible endpoint
    base_url = os.environ.get('AI_VISION_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
    model = os.environ.get('AI_VISION_MODEL', 'qwen-vl-max')

    raw = _safe_read_bytes(image_path)
    if not raw:
        raise RuntimeError('cannot read image bytes')

    # Resize image if it's too large (Qwen limit: 10MB base64 ~ 7.5MB raw)
    # We'll use Pillow to resize it to a reasonable size (e.g. max 1024px)
    try:
        from PIL import Image as PilImage
        import io
        
        with PilImage.open(io.BytesIO(raw)) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            # Resize if larger than 1024x1024 to reduce size
            max_dim = 1024
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim))
                
            # Save to buffer
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            raw = buf.getvalue()
            mime_type = 'image/jpeg'
    except Exception as e:
        # If resizing fails, try with original but it might fail API limit
        print(f"Image resize failed: {e}")
        pass

    b64 = base64.b64encode(raw).decode('ascii')
    
    if 'mime_type' not in locals():
        mime_type = 'image/jpeg'
        lower_path = image_path.lower()
        if lower_path.endswith('.png'):
            mime_type = 'image/png'
        elif lower_path.endswith('.webp'):
            mime_type = 'image/webp'
        elif lower_path.endswith('.gif'):
            mime_type = 'image/gif'

    prompt = (
        '请你分析这张图片内容，生成 1 到 8 个“标签”。\n'
        '标签要求：尽量用中文短词/短语（例如：海边、夕阳、猫、街景、婚礼、火锅、夜景、雪山），每个标签不超过 10 个汉字；不要输出长句子。\n'
        '输出格式要求：只输出 JSON 数组，例如：["海边","夕阳"]，不要输出任何多余文字。'
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64}"
                        }
                    }
                ]
            }
        ]
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'Qwen API request failed: {e.code} {e.reason} - {err_body}')
    except Exception as e:
        raise RuntimeError(f'Qwen API request failed: {e}')

    parsed = json.loads(body)
    
    text = None
    try:
        # OpenAI compatible response structure
        choices = parsed.get('choices') or []
        if choices:
            message = choices[0].get('message') or {}
            text = message.get('content')
    except Exception:
        text = None

    if not text:
        raise RuntimeError('unexpected AI response from Qwen')

    text = text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    try:
        arr = json.loads(text)
    except Exception:
        raise RuntimeError('AI did not return JSON array')

    if not isinstance(arr, list):
        raise RuntimeError('AI did not return list')

    tags: List[str] = []
    for x in arr:
        s = ('' if x is None else str(x)).strip()
        if not s:
            continue
        if len(s) > MAX_TAG_LEN:
            continue
        if s not in tags:
            tags.append(s)

        if len(tags) >= MAX_TAGS:
            break

    if not tags:
        raise RuntimeError('AI returned empty tags')

    return tags


def generate_ai_tags(image_path: str) -> List[str]:
    """Generate AI tags for an image.

    Only uses a real AI vision provider.
    If AI is not configured or the provider call fails, an exception is raised.
    """

    provider = (os.environ.get('AI_TAGGING_PROVIDER') or 'qwen').strip().lower()
    
    # Fallback for legacy config
    if provider in ['openai', 'gemini']:
        provider = 'qwen'

    if provider == 'qwen':
        return _qwen_vision_tags(image_path)
    else:
        raise RuntimeError(f'unsupported AI_TAGGING_PROVIDER: {provider}')
