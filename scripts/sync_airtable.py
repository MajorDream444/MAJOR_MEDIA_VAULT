#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import read_inventory_json  # noqa: E402
from src.media_vault.workflows import build_sync_payload, require_env, write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or run Airtable sync for inventory records.")
    parser.add_argument("--inventory", default="data/media_inventory.json", help="Input inventory JSON.")
    parser.add_argument("--output", default="exports/airtable_sync_payload.json", help="Dry-run payload output.")
    parser.add_argument("--write", action="store_true", help="Validate live env for future sync. No live API call is implemented yet.")
    args = parser.parse_args()

    records = read_inventory_json(Path(args.inventory))
    if args.write:
        require_env(["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID", "AIRTABLE_TABLE_NAME"])
    payload = build_sync_payload(records, "airtable")
    write_json(payload, Path(args.output))
    print(f"Prepared Airtable sync payload for {len(records)} records: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
