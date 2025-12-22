import json
import os
from pathlib import Path
from typing import Dict, Optional


def _parse_dotenv(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        raw = path.read_text(encoding='utf-8')
    except Exception:
        return data

    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if '=' not in s:
            continue
        k, v = s.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not k:
            continue
        data[k] = v
    return data


def _read_json(path: Path) -> Dict[str, str]:
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    if not isinstance(obj, dict):
        return {}

    out: Dict[str, str] = {}
    for k, v in obj.items():
        if not isinstance(k, str):
            continue
        if v is None:
            continue
        out[k] = str(v)
    return out


def load_runtime_config(base_dir: Optional[Path] = None) -> None:
    """Load runtime configuration into os.environ.

    Precedence (highest to lowest):
    1) existing os.environ (never overwritten)
    2) config/app_config.json
    3) .env

    This allows both local runs and Docker (with code mounted) to work
    without hard-coding secrets in code.
    """

    if base_dir is None:
        # backend/config/runtime_config.py -> backend/
        base_dir = Path(__file__).resolve().parent.parent

    json_path = base_dir / 'config' / 'app_config.json'
    env_path = base_dir / '.env'

    merged: Dict[str, str] = {}
    if env_path.exists():
        merged.update(_parse_dotenv(env_path))
    if json_path.exists():
        # json overrides .env
        merged.update(_read_json(json_path))

    for k, v in merged.items():
        if k not in os.environ and v is not None and str(v).strip() != '':
            os.environ[k] = str(v)
