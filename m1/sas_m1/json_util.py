from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(obj: Any) -> str:
    if isinstance(obj, dict):
        data = canonical_json(obj)
    elif isinstance(obj, str):
        data = obj
    else:
        data = canonical_json(obj)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
