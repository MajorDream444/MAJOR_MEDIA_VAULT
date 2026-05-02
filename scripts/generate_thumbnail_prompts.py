#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.io_utils import read_json_safe, read_text_safe, write_text_safe  # noqa: E402

YOUTUBE_TEMPLATE_PATH = REPO_ROOT / "config" / "design_templates" / "youtube_thumbnail_premium.md"


PROMPT_SPECS = {
    "youtube_thumbnail_prompt.md": {
        "title": "YouTube Thumbnail Prompt",
        "platform": "YouTube",
        "aspect_ratio": "16:9",
        "headline": "THE SYSTEM UNDER THE MOMENT",
    },
    "vertical_cover_prompt.md": {
        "title": "TikTok/Reels Cover Prompt",
        "platform": "TikTok, Instagram Reels, YouTube Shorts",
        "aspect_ratio": "9:16",
        "headline": "WATCH THE PATTERN",
    },
    "square_cover_prompt.md": {
        "title": "Instagram Square Prompt",
        "platform": "Instagram square feed",
        "aspect_ratio": "1:1",
        "headline": "THE HIDDEN LEVER",
    },
    "substack_header_prompt.md": {
        "title": "Substack Header Prompt",
        "platform": "Substack",
        "aspect_ratio": "16:9",
        "headline": "NOTES FROM THE SYSTEM",
    },
    "podcast_cover_prompt.md": {
        "title": "Podcast Cover Prompt",
        "platform": "Podcast cover art",
        "aspect_ratio": "1:1",
        "headline": "MAJOR MEDIA VAULT",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AI design prompts from an asset package.")
    parser.add_argument("--asset-package-dir", required=True, help="Asset package folder containing metadata, summary, transcript, and manifest files.")
    return parser.parse_args()


def resolve_package_dir(path: Path) -> Path:
    package_dir = path.expanduser().resolve()
    if (package_dir / "asset_manifest.json").exists():
        return package_dir
    candidates = [child for child in package_dir.iterdir() if child.is_dir() and (child / "asset_manifest.json").exists()]
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(f"Could not find a single asset package under: {package_dir}")


def read_text(path: Path, default: str = "") -> str:
    return read_text_safe(path) or default


def read_json(path: Path) -> Dict[str, object]:
    return read_json_safe(path)


def compact(text: str, limit: int = 900) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def youtube_design_template() -> str:
    if not YOUTUBE_TEMPLATE_PATH.exists():
        return ""
    return read_text(YOUTUBE_TEMPLATE_PATH).strip()


def source_description(metadata: Dict[str, object], manifest: Dict[str, object]) -> str:
    inventory = metadata.get("inventory_record", {})
    if not isinstance(inventory, dict):
        inventory = {}
    file_name = inventory.get("original_file_name") or Path(str(manifest.get("source_path", "media file"))).name
    file_type = inventory.get("file_type") or manifest.get("file_type") or "media"
    return f"{file_name} ({file_type})"


def build_prompt(spec: Dict[str, str], package_dir: Path, summary: str, transcript: str, metadata: Dict[str, object], manifest: Dict[str, object]) -> str:
    subject = source_description(metadata, manifest)
    context = compact(summary or transcript or "No transcript or summary exists yet. Use the metadata and creator documentary direction.")
    lines = [
        f"# {spec['title']}",
        "",
        f"- Platform: {spec['platform']}",
        f"- Exact aspect ratio: {spec['aspect_ratio']}",
        f"- Headline text: {spec['headline']}",
        "- Emotional tone: premium creator/founder documentary look, focused, intelligent, high-stakes, cinematic, calm authority.",
        f"- Subject description: {subject}",
        "- Visual concept: one strong subject, one clear idea, editorial lighting, premium media intelligence aesthetic.",
        "- Background style: clean cinematic depth, subtle texture, no clutter, no generic stock-photo feel.",
        "- Readable text guidance: use large high-contrast text, few words, generous spacing, readable on mobile.",
        "- Composition: strong focal point, clear hierarchy, no clutter, no tiny details, no crowded collage.",
        "- Avoid: messy overlays, unreadable text, cheap clickbait, random icons, extra faces, unrelated props.",
    ]
    if spec["platform"] == "YouTube":
        template = youtube_design_template()
        if template:
            lines.extend(["", "## Saved Design Template", "", template])
    lines.extend(
        [
            "",
            "## Source Context",
            "",
            context,
            "",
            "## Package",
            "",
            f"- Asset package: `{package_dir}`",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    package_dir = resolve_package_dir(Path(parse_args().asset_package_dir))
    prompts_dir = package_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    summary = read_text(package_dir / "summary.md")
    transcript = read_text(package_dir / "transcript.txt")
    metadata = read_json(package_dir / "metadata.json")
    manifest = read_json(package_dir / "asset_manifest.json")

    for file_name, spec in PROMPT_SPECS.items():
        prompt = build_prompt(spec, package_dir, summary, transcript, metadata, manifest)
        write_text_safe(prompts_dir / file_name, prompt)

    print(f"Wrote {len(PROMPT_SPECS)} thumbnail prompt files: {prompts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
