#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.workflows import transcribe_with_whisper  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe audio or video with the local Whisper CLI.")
    parser.add_argument("--input", required=True, help="Source audio/video path.")
    parser.add_argument("--output-dir", default="exports/transcripts", help="Output folder.")
    parser.add_argument("--model", default="base", help="Whisper model name.")
    parser.add_argument("--write", action="store_true", help="Actually run Whisper. Default is dry-run.")
    args = parser.parse_args()

    result = transcribe_with_whisper(Path(args.input), Path(args.output_dir), model=args.model, dry_run=not args.write)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
