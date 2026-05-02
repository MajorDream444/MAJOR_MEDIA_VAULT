#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS  # noqa: E402
from src.media_vault.workflows import write_json  # noqa: E402


PROCESS_STATUSES = {
    "skipped_missing_dependency",
    "skipped_not_applicable",
    "dry_run_ready",
    "processed",
    "failed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create safe processed-output packages from selected queue items.")
    parser.add_argument("--queue", required=True, help="Processing queue JSON path.")
    parser.add_argument("--output-dir", required=True, help="Processed package output directory.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum queue items to process. 0 means no limit.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode is the default.")
    parser.add_argument("--write", action="store_true", help="Actually create derived media outputs when dependencies exist.")
    return parser.parse_args()


def load_queue(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as queue_file:
        data = json.load(queue_file)
    if not isinstance(data, list):
        raise ValueError("Queue JSON must be a list.")
    return data


def detect_file_type(source_path: Path) -> str:
    extension = source_path.suffix.lower().lstrip(".")
    mime_type = mimetypes.guess_type(str(source_path))[0] or ""
    if mime_type.startswith("video/") or extension in VIDEO_EXTENSIONS:
        return "video"
    if mime_type.startswith("audio/") or extension in AUDIO_EXTENSIONS:
        return "audio"
    if mime_type.startswith("image/") or extension in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def command_result(status: str, reason: str, command: Optional[List[str]] = None, output_path: Optional[Path] = None) -> Dict[str, object]:
    if status not in PROCESS_STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    result: Dict[str, object] = {"status": status, "reason": reason}
    if command:
        result["command"] = command
    if output_path:
        result["output_path"] = str(output_path)
    return result


def run_command(command: List[str], output_path: Path, dry_run: bool) -> Dict[str, object]:
    if dry_run:
        return command_result("dry_run_ready", "Command is ready but --write was not passed.", command, output_path)
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Command failed with exit code {exc.returncode}.",
            "command": command,
            "output_path": str(output_path),
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    return {
        "status": "processed",
        "reason": "Derived output created.",
        "command": command,
        "output_path": str(output_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def ffmpeg_path(dry_run: bool) -> Optional[str]:
    found = shutil.which("ffmpeg")
    if found:
        return found
    if dry_run:
        return "ffmpeg"
    return None


def mov_to_mp4(source_path: Path, media_dir: Path, dry_run: bool) -> Dict[str, object]:
    if source_path.suffix.lower() != ".mov":
        return command_result("skipped_not_applicable", "MP4 conversion only applies to MOV sources.")
    ffmpeg = ffmpeg_path(dry_run)
    output_path = media_dir / f"{source_path.stem}_converted.mp4"
    if not ffmpeg:
        return command_result("skipped_missing_dependency", "ffmpeg is required for MOV to MP4 conversion.", output_path=output_path)
    command = [ffmpeg, "-y", "-i", str(source_path), "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output_path)]
    return run_command(command, output_path, dry_run=dry_run)


def extract_mp3(source_path: Path, media_dir: Path, file_type: str, dry_run: bool) -> Dict[str, object]:
    if file_type not in {"video", "audio"}:
        return command_result("skipped_not_applicable", "MP3 extraction only applies to video or audio sources.")
    ffmpeg = ffmpeg_path(dry_run)
    output_path = media_dir / f"{source_path.stem}_audio.mp3"
    if not ffmpeg:
        return command_result("skipped_missing_dependency", "ffmpeg is required for MP3 extraction.", output_path=output_path)
    command = [ffmpeg, "-y", "-i", str(source_path), "-vn", "-codec:a", "libmp3lame", "-q:a", "2", str(output_path)]
    return run_command(command, output_path, dry_run=dry_run)


def generate_thumbnail(source_path: Path, media_dir: Path, file_type: str, dry_run: bool) -> Dict[str, object]:
    if file_type not in {"video", "image"}:
        return command_result("skipped_not_applicable", "Thumbnail generation only applies to video or image sources.")
    ffmpeg = ffmpeg_path(dry_run)
    output_path = media_dir / f"{source_path.stem}_thumbnail.jpg"
    if not ffmpeg:
        return command_result("skipped_missing_dependency", "ffmpeg is required for thumbnail generation.", output_path=output_path)
    if file_type == "video":
        command = [ffmpeg, "-y", "-ss", "00:00:01", "-i", str(source_path), "-frames:v", "1", "-q:v", "2", str(output_path)]
    else:
        command = [ffmpeg, "-y", "-i", str(source_path), "-vf", "scale='min(1280,iw)':-2", "-frames:v", "1", str(output_path)]
    return run_command(command, output_path, dry_run=dry_run)


def selected_actions(task_type: str) -> List[str]:
    mapping = {
        "convert_mov": ["mov_to_mp4"],
        "extract_audio": ["extract_mp3"],
        "generate_thumbnail": ["thumbnail"],
        "visual_summary": ["thumbnail"],
        "transcribe": ["extract_mp3"],
    }
    return mapping.get(task_type, [])


def load_existing_manifest(manifest_path: Path) -> Dict[str, object]:
    if not manifest_path.exists():
        return {"runs": []}
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        data = json.load(manifest_file)
    if not isinstance(data, dict):
        return {"runs": []}
    data.setdefault("runs", [])
    return data


def write_notes(notes_path: Path, manifest: Dict[str, object]) -> None:
    lines = [
        "# Processing Notes",
        "",
        f"- Media ID: `{manifest.get('media_id', '')}`",
        f"- Source path: `{manifest.get('source_path', '')}`",
        "- Originals were not moved, renamed, modified, uploaded, deleted, or copied.",
        "",
        "## Runs",
        "",
    ]
    for run in manifest.get("runs", []):
        lines.append(f"### Queue Item `{run.get('queue_id', '')}`")
        lines.append("")
        lines.append(f"- Task type: `{run.get('task_type', '')}`")
        lines.append(f"- Mode: `{run.get('mode', '')}`")
        for action in run.get("actions", []):
            lines.append(f"- {action.get('action')}: `{action.get('status')}` - {action.get('reason')}")
        lines.append("")
    notes_path.write_text("\n".join(lines), encoding="utf-8")


def process_queue_item(queue_item: Dict[str, object], output_dir: Path, dry_run: bool) -> Dict[str, object]:
    media_id = str(queue_item.get("media_id", "unknown_media"))
    task_type = str(queue_item.get("task_type", "unknown_task"))
    source_path = Path(str(queue_item.get("source_path", ""))).expanduser().resolve()
    file_type = detect_file_type(source_path)
    media_dir = output_dir / media_id
    media_dir.mkdir(parents=True, exist_ok=True)

    action_names = selected_actions(task_type)
    if not action_names:
        action_results = [command_result("skipped_not_applicable", f"No processed-output action is mapped for task_type={task_type}.")]
    else:
        action_results = []
        for action_name in action_names:
            if action_name == "mov_to_mp4":
                result = mov_to_mp4(source_path, media_dir, dry_run=dry_run)
            elif action_name == "extract_mp3":
                result = extract_mp3(source_path, media_dir, file_type, dry_run=dry_run)
            elif action_name == "thumbnail":
                result = generate_thumbnail(source_path, media_dir, file_type, dry_run=dry_run)
            else:
                result = command_result("skipped_not_applicable", f"Unknown action: {action_name}")
            result["action"] = action_name
            action_results.append(result)

    manifest_path = media_dir / "processing_manifest.json"
    notes_path = media_dir / "processing_notes.md"
    manifest = load_existing_manifest(manifest_path)
    manifest.update(
        {
            "media_id": media_id,
            "source_path": str(source_path),
            "file_type": file_type,
            "output_dir": str(media_dir),
            "copy_originals": False,
            "source_safety": "Originals were not moved, renamed, modified, uploaded, deleted, or copied.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    manifest["runs"].append(
        {
            "queue_id": queue_item.get("queue_id"),
            "task_type": task_type,
            "mode": "dry_run" if dry_run else "write",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actions": action_results,
        }
    )
    write_json(manifest, manifest_path)
    write_notes(notes_path, manifest)

    return {
        "media_id": media_id,
        "queue_id": queue_item.get("queue_id"),
        "task_type": task_type,
        "source_path": str(source_path),
        "manifest_path": str(manifest_path),
        "notes_path": str(notes_path),
        "actions": action_results,
    }


def main() -> int:
    args = parse_args()
    dry_run = not args.write
    queue_path = Path(args.queue).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    queue = load_queue(queue_path)
    selected = queue[: args.limit] if args.limit else queue
    results = [process_queue_item(queue_item, output_dir, dry_run=dry_run) for queue_item in selected]

    report = {
        "queue_path": str(queue_path),
        "output_dir": str(output_dir),
        "mode": "dry_run" if dry_run else "write",
        "selected_count": len(selected),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_safety": "Originals were not moved, renamed, modified, uploaded, deleted, or copied.",
        "results": results,
    }
    write_json(report, output_dir / "processing_run_report.json")

    print(f"Processed {len(selected)} queue items in {'dry-run' if dry_run else 'write'} mode.")
    print(f"Wrote processing report: {output_dir / 'processing_run_report.json'}")
    print("Original source files were not moved, renamed, modified, uploaded, deleted, or copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
