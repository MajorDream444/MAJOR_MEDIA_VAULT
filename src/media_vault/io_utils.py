from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def read_text_safe(path: Path) -> str:
    source = Path(path)
    if not source.exists():
        return ""

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return source.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            break

    try:
        return source.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        return f"[read_error: {exc}]"


def read_json_safe(path: Path) -> Dict[str, Any]:
    source = Path(path)
    text = read_text_safe(source)
    if not text:
        return {}

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "_read_error": f"JSON parse failed: {exc}",
            "_source_path": str(source),
            "_raw_preview": text[:500],
        }

    sanitized = sanitize_for_json(data)
    if isinstance(sanitized, dict):
        return sanitized
    return {
        "_read_error": "JSON root was not an object.",
        "_source_path": str(source),
        "_raw_preview": text[:500],
        "value": sanitized,
    }


def write_text_safe(path: Path, content: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(str(content).rstrip() + "\n", encoding="utf-8")


def write_json_safe(path: Path, data: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_for_json(data)
    with output.open("w", encoding="utf-8") as output_file:
        json.dump(sanitized, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(sanitize_for_json(key)): sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)
