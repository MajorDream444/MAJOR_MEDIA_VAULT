#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.workflows import summarize_with_local_model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local/Kimi summary placeholder for a transcript or metadata file.")
    parser.add_argument("--input", required=True, help="Transcript, metadata, or inventory path.")
    parser.add_argument("--output-dir", default="exports/summaries", help="Output folder.")
    parser.add_argument("--provider", default="local", choices=["local", "kimi"], help="Summary provider label.")
    parser.add_argument("--model", default="kimi", help="Model label.")
    parser.add_argument("--write", action="store_true", help="Create a non-dry-run placeholder. No API call is made.")
    args = parser.parse_args()

    result = summarize_with_local_model(
        Path(args.input),
        Path(args.output_dir),
        provider=args.provider,
        model=args.model,
        dry_run=not args.write,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
