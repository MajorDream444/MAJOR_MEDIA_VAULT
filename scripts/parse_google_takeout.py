#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.inventory import scan_folder, write_inventory_csv, write_inventory_json  # noqa: E402
from src.media_vault.workflows import write_json  # noqa: E402


def find_takeout_sidecars(root: Path) -> list[dict[str, str]]:
    sidecars = []
    for sidecar in sorted(root.rglob("*.json")):
        media_candidate = sidecar.with_suffix("")
        sidecars.append({
            "sidecar_path": str(sidecar.resolve()),
            "likely_media_path": str(media_candidate.resolve()),
            "likely_media_exists": str(media_candidate.exists()),
        })
    return sidecars


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a Google Takeout folder into inventory and sidecar maps.")
    parser.add_argument("--path", required=True, help="Google Takeout folder path.")
    parser.add_argument("--output", default="data/google_takeout_inventory.csv", help="CSV inventory output.")
    parser.add_argument("--json-output", default="data/google_takeout_inventory.json", help="JSON inventory output.")
    parser.add_argument("--sidecars-output", default="data/google_takeout_sidecars.json", help="Sidecar map output.")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    records = scan_folder(root)
    sidecars = find_takeout_sidecars(root)
    write_inventory_csv(records, Path(args.output))
    write_inventory_json(records, Path(args.json_output))
    write_json(sidecars, Path(args.sidecars_output))
    print(json.dumps({"records": len(records), "sidecars": len(sidecars)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
