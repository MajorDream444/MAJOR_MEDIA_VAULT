from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.media_vault.io_utils import write_json_safe


COMMON_TOOL_DIRS = [
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
    Path("/opt/local/bin"),
]


def find_tool(tool_name: str) -> Optional[str]:
    executable = shutil.which(tool_name)
    if executable:
        return executable
    for tool_dir in COMMON_TOOL_DIRS:
        candidate = tool_dir / tool_name
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def ensure_tool(tool_name: str) -> str:
    executable = find_tool(tool_name)
    if not executable:
        raise RuntimeError(f"Required tool not found on PATH: {tool_name}")
    return executable


def tool_command(tool_name: str, dry_run: bool) -> str:
    if dry_run:
        return find_tool(tool_name) or tool_name
    return ensure_tool(tool_name)


def safe_output_path(source_path: Path, output_dir: Path, suffix: str, extension: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_stem = source_path.stem.replace("/", "_").replace(" ", "_")
    return output_dir / f"{clean_stem}{suffix}.{extension.lstrip('.')}"


def run_command(command: List[str], dry_run: bool = True) -> Dict[str, object]:
    if dry_run:
        return {"status": "dry_run", "command": command}
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return {
        "status": "completed",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def convert_mov_to_mp4(source_path: Path, output_dir: Path, dry_run: bool = True) -> Dict[str, object]:
    ffmpeg = tool_command("ffmpeg", dry_run)
    output_path = safe_output_path(source_path, output_dir, "_converted", "mp4")
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source_path),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = run_command(command, dry_run=dry_run)
    result["output_path"] = str(output_path)
    return result


def extract_audio_mp3(source_path: Path, output_dir: Path, dry_run: bool = True) -> Dict[str, object]:
    ffmpeg = tool_command("ffmpeg", dry_run)
    output_path = safe_output_path(source_path, output_dir, "_audio", "mp3")
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    ]
    result = run_command(command, dry_run=dry_run)
    result["output_path"] = str(output_path)
    return result


def generate_thumbnail(source_path: Path, output_dir: Path, timestamp: str = "00:00:01", dry_run: bool = True) -> Dict[str, object]:
    ffmpeg = tool_command("ffmpeg", dry_run)
    output_path = safe_output_path(source_path, output_dir, "_thumbnail", "jpg")
    command = [
        ffmpeg,
        "-y",
        "-ss",
        timestamp,
        "-i",
        str(source_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    result = run_command(command, dry_run=dry_run)
    result["output_path"] = str(output_path)
    return result


def transcribe_with_whisper(source_path: Path, output_dir: Path, model: str = "base", dry_run: bool = True) -> Dict[str, object]:
    whisper = tool_command("whisper", dry_run)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        whisper,
        str(source_path),
        "--model",
        model,
        "--output_dir",
        str(output_dir),
        "--output_format",
        "json",
    ]
    return run_command(command, dry_run=dry_run)


def summarize_with_local_model(input_path: Path, output_dir: Path, provider: str = "local", model: str = "kimi", dry_run: bool = True) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = safe_output_path(input_path, output_dir, f"_{provider}_summary", "json")
    payload = {
        "source_path": str(input_path),
        "provider": provider,
        "model": model,
        "status": "pending_model_integration" if dry_run else "manual_integration_required",
        "summary": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if dry_run:
        return {"status": "dry_run", "output_path": str(output_path), "payload": payload}
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2)
        output_file.write("\n")
    return {"status": "created_placeholder", "output_path": str(output_path)}


def build_sync_payload(records: Iterable[Dict[str, object]], destination: str) -> Dict[str, object]:
    return {
        "destination": destination,
        "status": "dry_run",
        "record_count": len(list(records)),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": "No live sync executed. Add credentials and explicit write mode before pushing records.",
    }


def require_env(keys: Iterable[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    missing = []
    for key in keys:
        value = os.environ.get(key)
        if value:
            values[key] = value
        else:
            missing.append(key)
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return values


def write_json(payload: object, output_path: Path) -> None:
    write_json_safe(output_path, payload)
