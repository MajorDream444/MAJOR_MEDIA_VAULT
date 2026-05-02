#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


SOURCE_SAFETY = "Original was not moved, renamed, modified, uploaded, or deleted."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate platform-ready publishing drafts from an asset package.")
    parser.add_argument("--asset-package-dir", required=True, help="Asset package folder, or parent folder containing one package.")
    parser.add_argument("--output-dir", help="Optional output directory. Defaults to asset_package_dir/content_package.")
    return parser.parse_args()


def resolve_package_dir(path: Path) -> Path:
    package_dir = path.expanduser().resolve()
    if (package_dir / "asset_manifest.json").exists():
        return package_dir
    candidates = [child for child in package_dir.iterdir() if child.is_dir() and (child / "asset_manifest.json").exists()]
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(f"Could not find a single asset package under: {package_dir}")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data if isinstance(data, dict) else {}


def compact(text: str, limit: int = 1200) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)
        json_file.write("\n")


def prompt_files(package_dir: Path) -> Dict[str, str]:
    prompts_dir = package_dir / "prompts"
    if not prompts_dir.exists():
        return {}
    return {path.name: read_text(path) for path in sorted(prompts_dir.glob("*.md"))}


def source_info(metadata: Dict[str, object], manifest: Dict[str, object]) -> Dict[str, str]:
    inventory = metadata.get("inventory_record", {})
    if not isinstance(inventory, dict):
        inventory = {}
    source_path = str(manifest.get("source_path") or inventory.get("source_path") or "")
    file_name = str(inventory.get("original_file_name") or Path(source_path).name or "Untitled media")
    file_type = str(inventory.get("file_type") or manifest.get("file_type") or "media")
    media_id = str(inventory.get("media_id") or manifest.get("media_id") or "unknown_media")
    return {
        "media_id": media_id,
        "file_name": file_name,
        "file_type": file_type,
        "source_path": source_path,
    }


def content_context(summary: str, transcript: str, metadata: Dict[str, object], manifest: Dict[str, object]) -> str:
    info = source_info(metadata, manifest)
    if transcript.strip():
        return compact(transcript, 1400)
    if summary.strip():
        return compact(summary, 1400)
    return (
        f"Placeholder: no transcript or summary is available yet for {info['file_name']}. "
        "Use the metadata and asset notes as a first-pass publishing draft source."
    )


def bullet_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def prompt_or_fallback(prompts: Dict[str, str], prompt_name: str, fallback: str) -> str:
    content = prompts.get(prompt_name, "").strip()
    return content if content else fallback


def youtube_outputs(info: Dict[str, str], context: str, prompts: Dict[str, str]) -> Dict[str, str]:
    base = Path(info["file_name"]).stem.replace("_", " ").strip() or "Untitled Media"
    thumbnail_fallback = "\n".join(
        [
            "# YouTube Thumbnail Prompt",
            "",
            "- Platform: YouTube",
            "- Exact aspect ratio: 16:9",
            f"- Subject description: {info['file_name']} ({info['file_type']})",
            "- Visual concept: premium creator/founder documentary look.",
            "- Headline text: THE SYSTEM UNDER THE MOMENT",
            "- Composition: subject on one side, bold headline on the other, strong negative space, readable on mobile, no clutter.",
        ]
    )
    return {
        "youtube/title_options.md": "\n".join(
            [
                "# YouTube Title Options",
                "",
                bullet_list(
                    [
                        f"{base}: The Story Behind the Moment",
                        f"What {base} Reveals",
                        f"The System Under {base}",
                        f"{base} Explained Like a Founder Lesson",
                        f"Why {base} Matters Now",
                    ]
                ),
            ]
        ),
        "youtube/description.md": "\n".join(
            [
                "# YouTube Description",
                "",
                f"This video draft is based on `{info['file_name']}`.",
                "",
                "## Draft",
                "",
                "A focused breakdown of the moment, the context around it, and the deeper system it points to.",
                "",
                "## Source Context",
                "",
                context,
                "",
                "Original media remains preserved. This is a derived publishing draft only.",
            ]
        ),
        "youtube/tags.txt": "\n".join(["media intelligence", "creator economy", "founder lessons", "documentary", "AI workflow", info["file_type"]]),
        "youtube/thumbnail_prompt.md": prompt_or_fallback(prompts, "youtube_thumbnail_prompt.md", thumbnail_fallback),
        "youtube/chapters.md": "\n".join(
            [
                "# YouTube Chapters",
                "",
                "00:00 Opening context",
                "00:30 What is happening",
                "01:30 The deeper pattern",
                "03:00 Why it matters",
                "04:30 Takeaway",
                "",
                "Placeholder chapters. Replace timestamps after final edit.",
            ]
        ),
    }


def tiktok_outputs(info: Dict[str, str], context: str, prompts: Dict[str, str]) -> Dict[str, str]:
    cover_fallback = "\n".join(
        [
            "# TikTok/Reels Cover Prompt",
            "",
            "- Platform: TikTok, Instagram Reels, YouTube Shorts",
            "- Exact aspect ratio: 9:16",
            f"- Subject description: {info['file_name']} ({info['file_type']})",
            "- Visual concept: cinematic vertical creator cover, strong subject focus, premium documentary feel.",
            "- Headline text: WATCH THE PATTERN",
            "- Composition: centered mobile-safe subject, bold readable text, no clutter, no tiny text.",
        ]
    )
    return {
        "tiktok_reels/hook_options.md": "\n".join(
            [
                "# TikTok/Reels Hook Options",
                "",
                bullet_list(
                    [
                        "Most people missed the real story here.",
                        "This is not just content. It is a signal.",
                        "Here is the system underneath the moment.",
                        "Watch what this reveals about leverage.",
                        "This clip explains more than it seems.",
                    ]
                ),
            ]
        ),
        "tiktok_reels/caption_options.md": "\n".join(
            [
                "# TikTok/Reels Caption Options",
                "",
                bullet_list(
                    [
                        f"Turning `{info['file_name']}` into a system-level read.",
                        "The moment is small. The pattern is not.",
                        "Save this if you study media, leverage, and culture.",
                    ]
                ),
                "",
                "## Context",
                "",
                context,
            ]
        ),
        "tiktok_reels/cover_prompt.md": prompt_or_fallback(prompts, "vertical_cover_prompt.md", cover_fallback),
        "tiktok_reels/hashtags.txt": "\n".join(["#mediaintelligence", "#creatorstrategy", "#founderlessons", "#documentary", "#aiworkflow"]),
    }


def substack_outputs(info: Dict[str, str], context: str) -> Dict[str, str]:
    return {
        "substack/essay_seed.md": "\n".join(
            [
                "# Essay Seed",
                "",
                f"Working source: `{info['file_name']}`",
                "",
                "## Thesis",
                "",
                "This media object is useful because it captures a moment that can be translated into a broader system, lesson, or cultural signal.",
                "",
                "## Source Context",
                "",
                context,
            ]
        ),
        "substack/headline_options.md": "\n".join(
            [
                "# Substack Headline Options",
                "",
                bullet_list(
                    [
                        "The System Under the Moment",
                        "What This Media Object Reveals",
                        "A Founder Lesson Hidden in Plain Sight",
                        "Notes From the Archive",
                        "The Signal Inside the Clip",
                    ]
                ),
            ]
        ),
        "substack/intro.md": "\n".join(
            [
                "# Intro Draft",
                "",
                "Some media is not valuable because it is polished. It is valuable because it preserves signal.",
                "",
                f"`{info['file_name']}` should be treated as a starting point: catalog it, study it, extract the system, then decide whether it deserves to become public-facing work.",
            ]
        ),
        "substack/pull_quotes.md": "\n".join(
            [
                "# Pull Quotes",
                "",
                bullet_list(
                    [
                        "The archive is only useful when it becomes searchable intelligence.",
                        "A clip is content. A pattern is leverage.",
                        "Preserve the raw source. Publish the refined insight.",
                    ]
                ),
            ]
        ),
    }


def podcast_outputs(info: Dict[str, str], context: str) -> Dict[str, str]:
    return {
        "podcast/episode_title_options.md": "\n".join(
            [
                "# Episode Title Options",
                "",
                bullet_list(
                    [
                        "The System Under the Moment",
                        "Archive as Intelligence",
                        "From Media File to Meaning",
                        "The Signal Inside the Source",
                        "Creator Memory and Leverage",
                    ]
                ),
            ]
        ),
        "podcast/show_notes.md": "\n".join(
            [
                "# Show Notes",
                "",
                f"Source asset: `{info['file_name']}`",
                "",
                "## Episode Frame",
                "",
                "A conversation or solo breakdown about what this asset captures, why it matters, and how it can become reusable creator IP.",
                "",
                "## Source Context",
                "",
                context,
            ]
        ),
        "podcast/description.md": "\n".join(
            [
                "# Podcast Description",
                "",
                "This episode turns a single source asset into a broader conversation about memory, media, leverage, and the systems hiding inside everyday moments.",
            ]
        ),
    }


def agent_memory_outputs(info: Dict[str, str], context: str, prompts: Dict[str, str]) -> Dict[str, str]:
    prompt_names = ", ".join(sorted(prompts)) if prompts else "No prompt files present."
    return {
        "agent_memory/memory_card.md": "\n".join(
            [
                "# Memory Card",
                "",
                f"- Media ID: `{info['media_id']}`",
                f"- File name: `{info['file_name']}`",
                f"- File type: `{info['file_type']}`",
                f"- Source path: `{info['source_path']}`",
                f"- Source safety: {SOURCE_SAFETY}",
                f"- Prompt files: {prompt_names}",
                "",
                "## Reusable Context",
                "",
                context,
            ]
        ),
        "agent_memory/doctrine_notes.md": "\n".join(
            [
                "# Doctrine Notes",
                "",
                "- Preserve raw source.",
                "- Generate derived publishing drafts only.",
                "- Extract the system underneath the media.",
                "- Treat the asset as searchable IP.",
                "- Do not publish without human review.",
            ]
        ),
        "agent_memory/reusable_quotes.md": "\n".join(
            [
                "# Reusable Quotes",
                "",
                bullet_list(
                    [
                        "Every file becomes searchable IP.",
                        "The archive is not storage. It is leverage waiting for structure.",
                        "Classify before moving. Preserve before publishing.",
                    ]
                ),
            ]
        ),
    }


def build_outputs(package_dir: Path) -> Dict[str, str]:
    metadata = read_json(package_dir / "metadata.json")
    manifest = read_json(package_dir / "asset_manifest.json")
    summary = read_text(package_dir / "summary.md")
    transcript = read_text(package_dir / "transcript.txt")
    notes = read_text(package_dir / "asset_notes.md")
    prompts = prompt_files(package_dir)
    info = source_info(metadata, manifest)
    context = content_context(summary, transcript, metadata, manifest)
    if not transcript.strip():
        context += "\n\nPlaceholder note: transcript.txt is missing, so transcript-dependent copy needs review."
    if not summary.strip():
        context += "\n\nPlaceholder note: summary.md is missing, so summary-dependent copy needs review."
    if notes.strip():
        context += "\n\nAsset notes: " + compact(notes, 500)

    outputs: Dict[str, str] = {}
    for section in [
        youtube_outputs(info, context, prompts),
        tiktok_outputs(info, context, prompts),
        substack_outputs(info, context),
        podcast_outputs(info, context),
        agent_memory_outputs(info, context, prompts),
    ]:
        outputs.update(section)
    return outputs


def main() -> int:
    args = parse_args()
    package_dir = resolve_package_dir(Path(args.asset_package_dir))
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else package_dir / "content_package"
    outputs = build_outputs(package_dir)

    for relative_path, content in outputs.items():
        write_text(output_dir / relative_path, content)

    manifest = {
        "asset_package_dir": str(package_dir),
        "output_dir": str(output_dir),
        "source_safety": SOURCE_SAFETY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_files": sorted(outputs),
        "rules": [
            "Deterministic template-based generation.",
            "Publishing drafts are derived outputs only.",
            "Originals were not moved, renamed, modified, uploaded, or deleted.",
            "Human review required before publishing.",
        ],
    }
    write_json(output_dir / "content_package_manifest.json", manifest)
    print(f"Wrote content package with {len(outputs)} draft files: {output_dir}")
    print("Original was not moved, renamed, modified, uploaded, or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
