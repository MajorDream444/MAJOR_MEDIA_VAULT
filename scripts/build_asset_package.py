#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import (  # noqa: E402
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    build_media_record,
)
from src.media_vault.workflows import find_tool, write_json  # noqa: E402


SOURCE_SAFETY = "Original was not moved, renamed, modified, uploaded, or deleted."
STATUSES = {"skipped_missing_dependency", "skipped_not_applicable", "dry_run_ready", "processed", "failed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe derived asset package for one media file.")
    parser.add_argument("--input", required=True, help="Source media file path.")
    parser.add_argument("--output-dir", required=True, help="Directory where the media_id package folder will be created.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode is the default.")
    parser.add_argument("--write", action="store_true", help="Actually create derived outputs when dependencies are available.")
    parser.add_argument("--copy-original", action="store_true", help="Copy original into the package folder. Off by default.")
    parser.add_argument("--privacy-level", default="private", help="Default privacy level for metadata record.")
    parser.add_argument("--generate-thumbnails", action="store_true", help="Generate platform thumbnail outputs inside the asset package.")
    parser.add_argument("--generate-thumbnail-prompts", action="store_true", help="Generate AI thumbnail prompt files inside the asset package.")
    parser.add_argument("--thumbnail-preset", default="all", help="Thumbnail preset name or all.")
    return parser.parse_args()


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


def tool_path(tool_name: str) -> Optional[str]:
    return find_tool(tool_name)


def status_result(status: str, reason: str, output_path: Optional[Path] = None, command: Optional[List[str]] = None) -> Dict[str, object]:
    if status not in STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    result: Dict[str, object] = {"status": status, "reason": reason}
    if output_path:
        result["output_path"] = str(output_path)
    if command:
        result["command"] = command
    return result


def run_json_command(command: List[str]) -> Dict[str, object]:
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Command failed with exit code {exc.returncode}.",
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "reason": "Command completed but did not return valid JSON.",
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    return {"status": "processed", "reason": "Metadata extracted.", "command": command, "data": payload}


def ffprobe_metadata(source_path: Path) -> Dict[str, object]:
    ffprobe = tool_path("ffprobe")
    if not ffprobe:
        return {"status": "skipped_missing_dependency", "reason": "ffprobe is not installed."}
    command = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(source_path)]
    return run_json_command(command)


def exiftool_metadata(source_path: Path) -> Dict[str, object]:
    exiftool = tool_path("exiftool")
    if not exiftool:
        return {"status": "skipped_missing_dependency", "reason": "exiftool is not installed."}
    command = [exiftool, "-json", str(source_path)]
    return run_json_command(command)


def run_asset_command(command: List[str], output_path: Path, dry_run: bool) -> Dict[str, object]:
    if dry_run:
        return status_result("dry_run_ready", "Command is ready but --write was not passed.", output_path, command)
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Command failed with exit code {exc.returncode}.",
            "output_path": str(output_path),
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    return {
        "status": "processed",
        "reason": "Derived output created.",
        "output_path": str(output_path),
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def make_thumbnail(source_path: Path, package_dir: Path, file_type: str, dry_run: bool) -> Dict[str, object]:
    if file_type not in {"video", "image"}:
        return status_result("skipped_not_applicable", "Thumbnail only applies to video or image sources.", package_dir / "thumbnail.jpg")
    ffmpeg = tool_path("ffmpeg")
    output_path = package_dir / "thumbnail.jpg"
    if not ffmpeg:
        return status_result("skipped_missing_dependency", "ffmpeg is required to generate thumbnail.jpg.", output_path)
    if file_type == "video":
        command = [ffmpeg, "-y", "-ss", "00:00:01", "-i", str(source_path), "-frames:v", "1", "-q:v", "2", str(output_path)]
    else:
        command = [ffmpeg, "-y", "-i", str(source_path), "-vf", "scale='min(1280,iw)':-2", "-frames:v", "1", str(output_path)]
    return run_asset_command(command, output_path, dry_run)


def make_audio(source_path: Path, package_dir: Path, file_type: str, dry_run: bool) -> Dict[str, object]:
    if file_type not in {"video", "audio"}:
        return status_result("skipped_not_applicable", "audio.mp3 only applies to video or audio sources.", package_dir / "audio.mp3")
    ffmpeg = tool_path("ffmpeg")
    output_path = package_dir / "audio.mp3"
    if not ffmpeg:
        return status_result("skipped_missing_dependency", "ffmpeg is required to generate audio.mp3.", output_path)
    command = [ffmpeg, "-y", "-i", str(source_path), "-vn", "-codec:a", "libmp3lame", "-q:a", "2", str(output_path)]
    return run_asset_command(command, output_path, dry_run)


def make_converted_mp4(source_path: Path, package_dir: Path, dry_run: bool) -> Dict[str, object]:
    output_path = package_dir / "converted.mp4"
    if source_path.suffix.lower() != ".mov":
        return status_result("skipped_not_applicable", "converted.mp4 only applies to MOV sources.", output_path)
    ffmpeg = tool_path("ffmpeg")
    if not ffmpeg:
        return status_result("skipped_missing_dependency", "ffmpeg is required to generate converted.mp4.", output_path)
    command = [ffmpeg, "-y", "-i", str(source_path), "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output_path)]
    return run_asset_command(command, output_path, dry_run)


def make_transcript(source_path: Path, package_dir: Path, file_type: str, dry_run: bool) -> Dict[str, object]:
    output_path = package_dir / "transcript.txt"
    if file_type not in {"video", "audio"}:
        return status_result("skipped_not_applicable", "transcript.txt only applies to video or audio sources.", output_path)
    whisper = tool_path("whisper")
    if not whisper:
        return status_result("skipped_missing_dependency", "whisper is required to generate transcript.txt.", output_path)
    command = [whisper, str(source_path), "--output_dir", str(package_dir), "--output_format", "txt"]
    if dry_run:
        return status_result("dry_run_ready", "Command is ready but --write was not passed.", output_path, command)
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Command failed with exit code {exc.returncode}.",
            "output_path": str(output_path),
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    whisper_output = package_dir / f"{source_path.stem}.txt"
    if whisper_output.exists() and whisper_output != output_path:
        whisper_output.replace(output_path)
    if not output_path.exists():
        return {
            "status": "failed",
            "reason": "Whisper completed but transcript.txt was not created.",
            "output_path": str(output_path),
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    return {
        "status": "processed",
        "reason": "transcript.txt created.",
        "output_path": str(output_path),
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def copy_original(source_path: Path, package_dir: Path, dry_run: bool, copy_enabled: bool) -> Dict[str, object]:
    output_path = package_dir / source_path.name
    if not copy_enabled:
        return status_result("skipped_not_applicable", "Original copy was not requested. Pass --copy-original to copy it.", output_path)
    if dry_run:
        return status_result("dry_run_ready", "Original would be copied because --copy-original was passed, but --write was not passed.", output_path)
    try:
        shutil.copy2(str(source_path), str(output_path))
    except OSError as exc:
        return status_result("failed", f"Original copy failed: {exc}", output_path)
    return status_result("processed", "Original copied into package because --copy-original was passed.", output_path)


def write_summary_placeholder(package_dir: Path, source_path: Path, media_id: str, dry_run: bool) -> Dict[str, object]:
    output_path = package_dir / "summary.md"
    lines = [
        "# Asset Summary",
        "",
        f"- Media ID: `{media_id}`",
        f"- Source file: `{source_path.name}`",
        f"- Mode: `{'dry_run' if dry_run else 'write'}`",
        "- Status: local summarizer is not wired yet.",
        "",
        "## Placeholder",
        "",
        "Summary generation will be filled by a future local/Kimi/Ollama summarizer step.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return status_result("processed", "summary.md placeholder written.", output_path)


def write_asset_notes(package_dir: Path, manifest: Dict[str, object]) -> None:
    lines = [
        "# Asset Notes",
        "",
        f"- Media ID: `{manifest.get('media_id')}`",
        f"- Source path: `{manifest.get('source_path')}`",
        f"- Mode: `{manifest.get('mode')}`",
        f"- Source safety: {manifest.get('source_safety')}",
        "",
        "## Assets",
        "",
    ]
    assets = manifest.get("assets", {})
    if isinstance(assets, dict):
        for asset_name, asset_result in assets.items():
            if isinstance(asset_result, dict):
                lines.append(f"- `{asset_name}`: `{asset_result.get('status')}` - {asset_result.get('reason')}")
    lines.extend(["", "## Notes", "", "- Originals are preserved by policy.", "- Derived files live only in this package folder."])
    (package_dir / "asset_notes.md").write_text("\n".join(lines), encoding="utf-8")


def run_package_extension(command: List[str]) -> Dict[str, object]:
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Command failed with exit code {exc.returncode}.",
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    return {
        "status": "processed",
        "reason": "Package extension completed.",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_metadata(source_path: Path, privacy_level: str) -> Dict[str, object]:
    inventory_record = build_media_record(source_path, privacy_level=privacy_level)
    return {
        "source_safety": SOURCE_SAFETY,
        "inventory_record": inventory_record,
        "ffprobe": ffprobe_metadata(source_path),
        "exiftool": exiftool_metadata(source_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    args = parse_args()
    dry_run = not args.write
    source_path = Path(args.input).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"Input path is not a file: {source_path}")

    metadata = build_metadata(source_path, args.privacy_level)
    inventory_record = metadata["inventory_record"]
    media_id = str(inventory_record["media_id"])
    file_type = detect_file_type(source_path)
    package_dir = Path(args.output_dir).expanduser().resolve() / media_id
    package_dir.mkdir(parents=True, exist_ok=True)

    assets = {
        "metadata_json": status_result("processed", "metadata.json written.", package_dir / "metadata.json"),
        "thumbnail_jpg": make_thumbnail(source_path, package_dir, file_type, dry_run),
        "audio_mp3": make_audio(source_path, package_dir, file_type, dry_run),
        "converted_mp4": make_converted_mp4(source_path, package_dir, dry_run),
        "transcript_txt": make_transcript(source_path, package_dir, file_type, dry_run),
        "summary_md": write_summary_placeholder(package_dir, source_path, media_id, dry_run),
        "original_copy": copy_original(source_path, package_dir, dry_run, args.copy_original),
    }

    write_json(metadata, package_dir / "metadata.json")
    manifest = {
        "media_id": media_id,
        "source_path": str(source_path),
        "file_type": file_type,
        "mode": "dry_run" if dry_run else "write",
        "package_dir": str(package_dir),
        "copy_original": bool(args.copy_original),
        "source_safety": SOURCE_SAFETY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assets": assets,
    }
    write_json(manifest, package_dir / "asset_manifest.json")
    write_asset_notes(package_dir, manifest)

    extensions: Dict[str, object] = {}
    if args.generate_thumbnails:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_platform_thumbnails.py"),
            "--input",
            str(source_path),
            "--asset-package-dir",
            str(package_dir),
            "--preset",
            args.thumbnail_preset,
        ]
        if args.write:
            command.append("--write")
        extensions["thumbnails"] = run_package_extension(command)
    if args.generate_thumbnail_prompts:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_thumbnail_prompts.py"),
            "--asset-package-dir",
            str(package_dir),
        ]
        extensions["thumbnail_prompts"] = run_package_extension(command)
    if extensions:
        manifest["extensions"] = extensions
        write_json(manifest, package_dir / "asset_manifest.json")
        write_asset_notes(package_dir, manifest)

    print(f"Built asset package in {'dry-run' if dry_run else 'write'} mode: {package_dir}")
    print("Original was not moved, renamed, modified, uploaded, or deleted.")
    if not args.copy_original:
        print("Original was not copied. Pass --copy-original to include a copy in the package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
