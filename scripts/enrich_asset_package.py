#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.io_utils import read_json_safe, read_text_safe, write_json_safe, write_text_safe  # noqa: E402

LOCAL_MODELS_PATH = REPO_ROOT / "config" / "local_models.json"
SOURCE_SAFETY = "Original was not moved, renamed, modified, uploaded, or deleted."


OUTPUT_SPECS = {
    "visual_summary.md": {
        "title": "Visual Summary",
        "instruction": "Create a concise visual summary. If visual context is limited, infer only from filenames, metadata, notes, and prompts.",
    },
    "narrative_summary.md": {
        "title": "Narrative Summary",
        "instruction": "Summarize the narrative, context, likely story, and publishing value of this asset.",
    },
    "seo_tags.md": {
        "title": "SEO Tags",
        "instruction": "Generate platform-safe SEO tags, search phrases, and topic clusters.",
    },
    "title_options.md": {
        "title": "Title Options",
        "instruction": "Generate punchy title options for YouTube, Substack, podcast, and short-form use.",
    },
    "clip_ideas.md": {
        "title": "Clip Ideas",
        "instruction": "Generate short-form clip ideas, hooks, and edit concepts.",
    },
    "substack_angles.md": {
        "title": "Substack Angles",
        "instruction": "Generate essay angles and newsletter frames.",
    },
    "agent_memory_enriched.md": {
        "title": "Agent Memory Enriched",
        "instruction": "Generate reusable structured memory for future agents. Keep it concrete, searchable, and evidence-aware.",
    },
    "privacy_review.md": {
        "title": "Privacy Review",
        "instruction": "Generate a cautious privacy and publishing review. Flag unknowns and require human review.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich an asset package with local Ollama/Kimi-compatible models.")
    parser.add_argument("--asset-package-dir", required=True, help="Asset package folder, or parent folder containing one package.")
    parser.add_argument("--model", help="Ollama model name. Defaults to config/local_models.json default_model.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode is the default.")
    parser.add_argument("--write", action="store_true", help="Call Ollama and write enriched outputs.")
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
    return read_text_safe(path)


def read_json(path: Path) -> Dict[str, object]:
    return read_json_safe(path)


def write_text(path: Path, content: str) -> None:
    write_text_safe(path, content)


def write_json(path: Path, payload: object) -> None:
    write_json_safe(path, payload)


def load_model_config() -> Dict[str, object]:
    config = read_json(LOCAL_MODELS_PATH)
    if not config:
        return {"default_model": "kimi", "fallback_model": "llama3.2", "tasks": {}}
    return config


def find_ollama() -> Optional[str]:
    for candidate in ["ollama", "/opt/homebrew/bin/ollama", "/usr/local/bin/ollama"]:
        if candidate == "ollama":
            try:
                subprocess.run([candidate, "--version"], check=True, capture_output=True, text=True)
                return candidate
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        path = Path(candidate)
        if path.exists() and path.is_file():
            return str(path)
    return None


def list_ollama_models(ollama: str) -> List[str]:
    try:
        completed = subprocess.run([ollama, "list"], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    models: List[str] = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0].split(":")[0])
            models.append(parts[0])
    return sorted(set(models))


def prompt_files(package_dir: Path) -> Dict[str, str]:
    prompts_dir = package_dir / "prompts"
    if not prompts_dir.exists():
        return {}
    return {path.name: read_text(path) for path in sorted(prompts_dir.glob("*.md"))}


def compact(text: str, limit: int = 5000) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def asset_context(package_dir: Path) -> Dict[str, object]:
    metadata = read_json(package_dir / "metadata.json")
    manifest = read_json(package_dir / "asset_manifest.json")
    transcript = read_text(package_dir / "transcript.txt")
    summary = read_text(package_dir / "summary.md")
    notes = read_text(package_dir / "asset_notes.md")
    prompts = prompt_files(package_dir)
    context_level = "normal" if transcript.strip() else "low_context"
    warnings = []
    for name, payload in [("metadata.json", metadata), ("asset_manifest.json", manifest)]:
        if payload.get("_read_error"):
            warnings.append(f"{name}: {payload.get('_read_error')}")
    return {
        "metadata": metadata,
        "manifest": manifest,
        "transcript": transcript,
        "summary": summary,
        "asset_notes": notes,
        "thumbnail_prompts": prompts,
        "context_level": context_level,
        "warnings": warnings,
    }


def build_prompt(output_name: str, spec: Dict[str, str], context: Dict[str, object]) -> str:
    prompts = context.get("thumbnail_prompts", {})
    prompt_text = ""
    if isinstance(prompts, dict):
        prompt_text = "\n\n".join(f"## {name}\n{value}" for name, value in prompts.items())
    return "\n".join(
        [
            "You are enriching a local-first media asset package for MAJOR_MEDIA_VAULT.",
            "Return markdown only. Do not claim certainty where source context is missing.",
            "Human review is required before publishing.",
            f"Output file: {output_name}",
            f"Task: {spec['instruction']}",
            f"Context level: {context['context_level']}",
            "",
            "## Metadata",
            compact(json.dumps(context.get("metadata", {}), ensure_ascii=False, indent=2), 2500),
            "",
            "## Manifest",
            compact(json.dumps(context.get("manifest", {}), ensure_ascii=False, indent=2), 1800),
            "",
            "## Summary",
            compact(str(context.get("summary", "")) or "No summary.md available.", 1600),
            "",
            "## Transcript",
            compact(str(context.get("transcript", "")) or "No transcript.txt available. Mark output low_context.", 2600),
            "",
            "## Asset Notes",
            compact(str(context.get("asset_notes", "")) or "No asset_notes.md available.", 1600),
            "",
            "## Thumbnail Prompts",
            compact(prompt_text or "No thumbnail prompt files available.", 2200),
        ]
    )


def deterministic_placeholder(title: str, output_name: str, context: Dict[str, object], reason: str, model: str) -> str:
    low_context = context["context_level"] == "low_context"
    lines = [
        f"# {title}",
        "",
        f"- Status: skipped",
        f"- Reason: {reason}",
        f"- Requested model: `{model}`",
        f"- Context level: `{'low_context' if low_context else 'normal'}`",
        f"- Source safety: {SOURCE_SAFETY}",
        "",
    ]
    if low_context:
        lines.extend(
            [
                "## Low Context Notice",
                "",
                "No transcript.txt was found. This enrichment should be treated as low-confidence and metadata-driven until transcription exists.",
                "",
            ]
        )
    lines.extend(
        [
            "## Draft Placeholder",
            "",
            f"This file is reserved for `{output_name}`. Run with `--write` after Ollama and the selected model are available to generate local AI enrichment.",
            "",
            "Human review is required before publishing.",
        ]
    )
    return "\n".join(lines)


def call_ollama(ollama: str, model: str, prompt: str) -> Dict[str, object]:
    command = [ollama, "run", model, prompt]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired as exc:
        return {"status": "failed", "reason": "Ollama call timed out.", "command": command, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "reason": f"Ollama exited with code {exc.returncode}.",
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    return {"status": "processed", "reason": "Ollama enrichment completed.", "command": command[:3] + ["<prompt>"], "stdout": completed.stdout, "stderr": completed.stderr}


def main() -> int:
    args = parse_args()
    dry_run = not args.write
    package_dir = resolve_package_dir(Path(args.asset_package_dir))
    enrichment_dir = package_dir / "enrichment"
    enrichment_dir.mkdir(parents=True, exist_ok=True)

    config = load_model_config()
    model = args.model or str(config.get("default_model", "kimi"))
    context = asset_context(package_dir)
    ollama = find_ollama()
    available_models = list_ollama_models(ollama) if ollama and args.write else []

    manifest: Dict[str, object] = {
        "asset_package_dir": str(package_dir),
        "enrichment_dir": str(enrichment_dir),
        "model": model,
        "mode": "dry_run" if dry_run else "write",
        "context_level": context["context_level"],
        "warnings": context.get("warnings", []),
        "source_safety": SOURCE_SAFETY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ollama_path": ollama or "",
        "available_models_checked": available_models,
        "outputs": {},
        "rules": [
            "Enrichment output is derived text only.",
            "Originals were not moved, renamed, modified, uploaded, or deleted.",
            "Human review required before publishing.",
        ],
    }

    if dry_run:
        skip_reason = "Dry-run only. Pass --write to call Ollama."
    elif not ollama:
        skip_reason = "Ollama is missing or not executable."
    elif available_models and model not in available_models:
        skip_reason = f"Model `{model}` is not available in Ollama."
    else:
        skip_reason = ""

    for output_name, spec in OUTPUT_SPECS.items():
        output_path = enrichment_dir / output_name
        if skip_reason:
            content = deterministic_placeholder(spec["title"], output_name, context, skip_reason, model)
            status = "dry_run_ready" if dry_run else "skipped"
            result: Dict[str, object] = {"status": status, "reason": skip_reason, "output_path": str(output_path)}
        else:
            response = call_ollama(str(ollama), model, build_prompt(output_name, spec, context))
            if response["status"] == "processed":
                content = str(response.get("stdout", "")).strip() or deterministic_placeholder(spec["title"], output_name, context, "Ollama returned empty output.", model)
            else:
                content = deterministic_placeholder(spec["title"], output_name, context, str(response.get("reason", "Ollama failed.")), model)
            result = {
                "status": response["status"],
                "reason": response["reason"],
                "output_path": str(output_path),
                "stderr": response.get("stderr", ""),
            }
        write_text(output_path, content)
        manifest["outputs"][output_name] = result

    write_json(enrichment_dir / "enrichment_manifest.json", manifest)
    print(f"Wrote enrichment package: {enrichment_dir}")
    print(f"Mode: {'dry-run' if dry_run else 'write'} | Model: {model} | Context: {context['context_level']}")
    print("Original was not moved, renamed, modified, uploaded, or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
