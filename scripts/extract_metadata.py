#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import build_media_record, scan_folder  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract metadata records for a file or folder.")
    parser.add_argument("--path", required=True, help="File or folder path to inspect.")
    parser.add_argument("--large-file-mb", type=float, default=100, help="Large file threshold in megabytes.")
    parser.add_argument("--privacy-level", default="private", help="Default privacy level for new records.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.path).expanduser().resolve()
    if target.is_dir():
        records = scan_folder(target, large_file_mb=args.large_file_mb, privacy_level=args.privacy_level)
    elif target.is_file():
        records = [build_media_record(target, large_file_mb=args.large_file_mb, privacy_level=args.privacy_level)]
    else:
        raise FileNotFoundError(f"Path does not exist: {target}")

    print(json.dumps(records, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
