#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import (  # noqa: E402
    build_processing_queue,
    scan_folder,
    write_inventory_csv,
    write_inventory_json,
    write_processing_queue,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a local media folder and generate inventory plus queue files.")
    parser.add_argument("--path", required=True, help="Folder path to scan recursively.")
    parser.add_argument("--output", default="data/media_inventory.csv", help="CSV inventory output path.")
    parser.add_argument("--json-output", default="data/media_inventory.json", help="JSON inventory output path.")
    parser.add_argument("--queue-output", default="queues/processing_queue.json", help="Processing queue output path.")
    parser.add_argument("--large-file-mb", type=float, default=100, help="Large file threshold in megabytes.")
    parser.add_argument("--privacy-level", default="private", help="Default privacy level for new records.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = scan_folder(Path(args.path), large_file_mb=args.large_file_mb, privacy_level=args.privacy_level)
    queue = build_processing_queue(records)

    csv_output = Path(args.output)
    json_output = Path(args.json_output)
    queue_output = Path(args.queue_output)

    write_inventory_csv(records, csv_output)
    write_inventory_json(records, json_output)
    write_processing_queue(queue, queue_output)

    print(f"Scanned {len(records)} files.")
    print(f"Wrote CSV inventory: {csv_output}")
    print(f"Wrote JSON inventory: {json_output}")
    print(f"Wrote processing queue: {queue_output}")
    print("Source files were not moved, renamed, modified, uploaded, or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
