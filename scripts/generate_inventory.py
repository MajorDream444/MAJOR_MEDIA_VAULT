#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import scan_folder, write_inventory_csv, write_inventory_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CSV and JSON media inventory files.")
    parser.add_argument("--path", required=True, help="Folder path to scan recursively.")
    parser.add_argument("--output", default="data/media_inventory.csv", help="CSV inventory output path.")
    parser.add_argument("--json-output", default="data/media_inventory.json", help="JSON inventory output path.")
    parser.add_argument("--large-file-mb", type=float, default=100, help="Large file threshold in megabytes.")
    parser.add_argument("--privacy-level", default="private", help="Default privacy level for new records.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = scan_folder(Path(args.path), large_file_mb=args.large_file_mb, privacy_level=args.privacy_level)
    write_inventory_csv(records, Path(args.output))
    write_inventory_json(records, Path(args.json_output))
    print(f"Wrote {len(records)} inventory records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
