#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import build_processing_queue, read_inventory_json, write_processing_queue  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a processing queue from a media inventory JSON file.")
    parser.add_argument("--inventory", default="data/media_inventory.json", help="Input inventory JSON path.")
    parser.add_argument("--output", default="queues/processing_queue.json", help="Processing queue output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = read_inventory_json(Path(args.inventory))
    queue = build_processing_queue(records)
    write_processing_queue(queue, Path(args.output))
    print(f"Wrote {len(queue)} queue tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
