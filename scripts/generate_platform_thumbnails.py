#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS  # noqa: E402
from src.media_vault.workflows import find_tool, write_json  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError  # type: ignore
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore

    class UnidentifiedImageError(Exception):
        pass


SOURCE_SAFETY = "Original was not moved, renamed, modified, uploaded, or deleted."
PRESETS_PATH = REPO_ROOT / "config" / "thumbnail_presets.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate platform-specific thumbnail and artwork ratios.")
    parser.add_argument("--input", required=True, help="Source image or video path.")
    parser.add_argument("--asset-package-dir", help="Optional asset package folder. Outputs default under its thumbnails folder.")
    parser.add_argument("--output-dir", help="Output directory. If asset package is passed, defaults to asset_package_dir/thumbnails.")
    parser.add_argument("--preset", default="all", help="Preset name or all.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode is the default.")
    parser.add_argument("--write", action="store_true", help="Actually generate derived JPG files.")
    return parser.parse_args()


def load_presets() -> Dict[str, Dict[str, object]]:
    with PRESETS_PATH.open("r", encoding="utf-8") as presets_file:
        data = json.load(presets_file)
    if not isinstance(data, dict):
        raise ValueError("thumbnail_presets.json must contain an object.")
    return data


def select_presets(all_presets: Dict[str, Dict[str, object]], preset_name: str) -> Dict[str, Dict[str, object]]:
    if preset_name == "all":
        return all_presets
    if preset_name not in all_presets:
        raise ValueError(f"Unknown preset: {preset_name}")
    return {preset_name: all_presets[preset_name]}


def detect_file_type(source_path: Path) -> str:
    extension = source_path.suffix.lower().lstrip(".")
    mime_type = mimetypes.guess_type(str(source_path))[0] or ""
    if mime_type.startswith("video/") or extension in VIDEO_EXTENSIONS:
        return "video"
    if mime_type.startswith("image/") or extension in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return Path(args.output_dir).expanduser().resolve()
    if args.asset_package_dir:
        return Path(args.asset_package_dir).expanduser().resolve() / "thumbnails"
    raise ValueError("--output-dir is required unless --asset-package-dir is provided.")


def status(status_name: str, reason: str, output_path: Optional[Path] = None, command: Optional[List[str]] = None) -> Dict[str, object]:
    result: Dict[str, object] = {"status": status_name, "reason": reason}
    if output_path:
        result["output_path"] = str(output_path)
    if command:
        result["command"] = command
    return result


def extract_video_frame(source_path: Path, work_dir: Path, dry_run: bool) -> Dict[str, object]:
    ffmpeg = find_tool("ffmpeg")
    frame_path = work_dir / "source_frame.jpg"
    if not ffmpeg:
        return status("skipped_missing_dependency", "ffmpeg is required to extract a video frame.", frame_path)
    command = [ffmpeg, "-y", "-ss", "00:00:01", "-i", str(source_path), "-frames:v", "1", "-q:v", "2", str(frame_path)]
    if dry_run:
        return status("dry_run_ready", "Video frame extraction command is ready.", frame_path, command)
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"ffmpeg frame extraction failed with exit code {exc.returncode}.",
            "output_path": str(frame_path),
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    return {
        "status": "processed",
        "reason": "Video frame extracted.",
        "output_path": str(frame_path),
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def open_source_image(source_path: Path, file_type: str, dry_run: bool, work_dir: Path) -> Dict[str, object]:
    if Image is None:
        return status("skipped_missing_dependency", "Pillow is required to read and resize images.")
    if file_type == "video":
        frame = extract_video_frame(source_path, work_dir, dry_run)
        if frame["status"] != "processed":
            return frame
        image_path = Path(str(frame["output_path"]))
    elif file_type == "image":
        image_path = source_path
    else:
        return status("skipped_not_applicable", "Input must be an image or video.")

    try:
        with Image.open(image_path) as img:
            return {"status": "processed", "reason": "Source image loaded.", "image": img.convert("RGB")}
    except (UnidentifiedImageError, OSError) as exc:
        return {"status": "fallback_placeholder", "reason": f"Source could not be decoded as an image: {exc}", "image": None}


def placeholder_image(width: int, height: int, label: str) -> Image.Image:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("Pillow is required to create placeholder images.")
    image = Image.new("RGB", (width, height), (18, 20, 24))
    draw = ImageDraw.Draw(image)
    accent = (238, 220, 170)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=accent, width=max(6, width // 160))
    font = ImageFont.load_default()
    lines = ["MAJOR MEDIA VAULT", label[:44], "Derived thumbnail placeholder"]
    line_height = 22
    y = max(20, (height - line_height * len(lines)) // 2)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = max(20, (width - (bbox[2] - bbox[0])) // 2)
        draw.text((x, y), line, fill=accent, font=font)
        y += line_height
    return image


def crop_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    src_width, src_height = image.size
    target_ratio = width / height
    src_ratio = src_width / src_height
    if src_ratio > target_ratio:
        new_width = int(src_height * target_ratio)
        left = (src_width - new_width) // 2
        box = (left, 0, left + new_width, src_height)
    else:
        new_height = int(src_width / target_ratio)
        top = (src_height - new_height) // 2
        box = (0, top, src_width, top + new_height)
    return image.crop(box).resize((width, height), Image.Resampling.LANCZOS)


def write_notes(output_dir: Path, manifest: Dict[str, object]) -> None:
    lines = [
        "# Thumbnails Notes",
        "",
        f"- Source path: `{manifest.get('source_path')}`",
        f"- Mode: `{manifest.get('mode')}`",
        f"- Source safety: {manifest.get('source_safety')}",
        "",
        "## Presets",
        "",
    ]
    for name, item in manifest.get("outputs", {}).items():
        lines.append(f"- `{name}`: `{item.get('status')}` - {item.get('reason')}")
    (output_dir / "thumbnails_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    dry_run = not args.write
    source_path = Path(args.input).expanduser().resolve()
    output_dir = resolve_output_dir(args)
    thumbnails_dir = output_dir / "thumbnails" if output_dir.name != "thumbnails" else output_dir
    thumbnails_dir.mkdir(parents=True, exist_ok=True)

    all_presets = load_presets()
    presets = select_presets(all_presets, args.preset)
    file_type = detect_file_type(source_path)
    manifest: Dict[str, object] = {
        "source_path": str(source_path),
        "file_type": file_type,
        "mode": "dry_run" if dry_run else "write",
        "source_safety": SOURCE_SAFETY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preset": args.preset,
        "outputs": {},
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        source_result = open_source_image(source_path, file_type, dry_run, Path(temp_dir))
        source_image = source_result.get("image")
        for preset_name, preset in presets.items():
            width = int(preset["width"])
            height = int(preset["height"])
            output_path = thumbnails_dir / f"{preset_name}.jpg"
            if dry_run:
                result = status("dry_run_ready", "Thumbnail output is ready to generate.", output_path)
            elif source_result["status"] in {"skipped_missing_dependency", "skipped_not_applicable", "failed"}:
                result = status(str(source_result["status"]), str(source_result["reason"]), output_path)
            else:
                image = source_image if isinstance(source_image, Image.Image) else placeholder_image(width, height, source_path.name)
                crop_resize(image, width, height).save(output_path, "JPEG", quality=92)
                result = status("processed", "Thumbnail generated as derived output.", output_path)
                if source_result["status"] == "fallback_placeholder":
                    result["source_decode_status"] = source_result["reason"]
            result["preset"] = preset
            manifest["outputs"][preset_name] = result

    write_json(manifest, thumbnails_dir / "thumbnails_manifest.json")
    write_notes(thumbnails_dir, manifest)
    print(f"Prepared {len(presets)} thumbnail preset outputs in {'dry-run' if dry_run else 'write'} mode: {thumbnails_dir}")
    print("Original was not moved, renamed, modified, uploaded, or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
