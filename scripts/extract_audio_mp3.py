#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.workflows import extract_audio_mp3  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract MP3 audio from a media file using ffmpeg.")
    parser.add_argument("--input", required=True, help="Source media path.")
    parser.add_argument("--output-dir", default="exports/audio", help="Output folder.")
    parser.add_argument("--write", action="store_true", help="Actually run ffmpeg. Default is dry-run.")
    args = parser.parse_args()

    result = extract_audio_mp3(Path(args.input), Path(args.output_dir), dry_run=not args.write)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
