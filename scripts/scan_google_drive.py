#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import build_processing_queue, scan_folder, write_inventory_csv, write_inventory_json, write_processing_queue  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a local Google Drive folder without using the Drive API.")
    parser.add_argument("--path", required=True, help="Local Google Drive folder path.")
    parser.add_argument("--output", default="data/google_drive_inventory.csv", help="CSV inventory output.")
    parser.add_argument("--json-output", default="data/google_drive_inventory.json", help="JSON inventory output.")
    parser.add_argument("--queue-output", default="queues/google_drive_processing_queue.json", help="Queue output.")
    args = parser.parse_args()

    records = scan_folder(Path(args.path))
    queue = build_processing_queue(records)
    write_inventory_csv(records, Path(args.output))
    write_inventory_json(records, Path(args.json_output))
    write_processing_queue(queue, Path(args.queue_output))
    print(f"Scanned local Google Drive folder with {len(records)} files. No cloud API call was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
