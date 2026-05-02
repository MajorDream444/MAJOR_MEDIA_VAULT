#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

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
    parser = argparse.ArgumentParser(description="Run a complete read-only media audit against a folder.")
    parser.add_argument("--path", required=True, help="Folder path to audit recursively.")
    parser.add_argument("--output-dir", required=True, help="Folder where audit artifacts should be written.")
    parser.add_argument("--large-file-mb", type=float, default=100, help="Large file threshold in megabytes.")
    parser.add_argument("--privacy-level", default="private", help="Default privacy level for new records.")
    return parser.parse_args()


def bool_value(record: Dict[str, object], field: str) -> bool:
    return bool(record.get(field))


def total_size_bytes(records: Iterable[Dict[str, object]]) -> int:
    return sum(int(record.get("file_size_bytes", 0)) for record in records)


def format_bytes(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size = float(size_bytes)
    for unit in ["KB", "MB", "GB", "TB"]:
        size /= 1024
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}"
    return f"{size_bytes} B"


def markdown_table(records: List[Dict[str, object]], columns: List[str], empty_message: str = "None found.") -> str:
    if not records:
        return empty_message

    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for record in records:
        values = [markdown_cell(record.get(column, "")) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *rows])


def markdown_cell(value: object) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def likely_archive_only(records: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    archive_extensions = {"pdf", "doc", "docx", "txt", "rtf", "md", "csv", "json", "xls", "xlsx", "ppt", "pptx"}
    results = []
    for record in records:
        file_type = str(record.get("file_type", ""))
        extension = str(record.get("extension", ""))
        if file_type == "document" or extension in archive_extensions:
            results.append(record)
    return results


def likely_content_gold(records: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    results = []
    for record in records:
        file_type = str(record.get("file_type", ""))
        is_camera = bool_value(record, "likely_camera_phone_media")
        needs_transcription = bool_value(record, "needs_transcription")
        needs_visual_summary = bool_value(record, "needs_visual_summary")
        if file_type in {"video", "audio"} or (file_type == "image" and is_camera) or needs_transcription or needs_visual_summary:
            results.append(record)
    return results


def build_audit_report(source_path: Path, output_dir: Path, records: List[Dict[str, object]], queue: List[Dict[str, object]]) -> str:
    counts = Counter(str(record.get("file_type", "unknown")) for record in records)
    largest_files = sorted(records, key=lambda record: int(record.get("file_size_bytes", 0)), reverse=True)[:20]
    mov_files = [record for record in records if bool_value(record, "needs_conversion")]
    transcription_files = [record for record in records if bool_value(record, "needs_transcription")]
    visual_summary_files = [record for record in records if bool_value(record, "needs_visual_summary")]
    enhancement_files = [record for record in records if bool_value(record, "needs_enhancement")]
    archive_only = likely_archive_only(records)
    content_gold = likely_content_gold(records)

    generated_at = datetime.now(timezone.utc).isoformat()
    total_bytes = total_size_bytes(records)
    table_columns = ["original_file_name", "file_type", "extension", "file_size_mb", "source_path"]

    lines = [
        "# MAJOR_MEDIA_VAULT Audit Report",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Source path: `{source_path}`",
        f"- Output directory: `{output_dir}`",
        "- Source safety: originals were not moved, renamed, modified, uploaded, or deleted.",
        "",
        "## Summary",
        "",
        f"- Total files: {len(records)}",
        f"- Total storage size: {format_bytes(total_bytes)}",
        f"- Video count: {counts.get('video', 0)}",
        f"- Audio count: {counts.get('audio', 0)}",
        f"- Image count: {counts.get('image', 0)}",
        f"- Document count: {counts.get('document', 0)}",
        f"- Unknown count: {counts.get('unknown', 0)}",
        f"- Processing queue tasks: {len(queue)}",
        "",
        "## Largest 20 Files",
        "",
        markdown_table(largest_files, table_columns),
        "",
        "## MOV Files Needing Conversion",
        "",
        markdown_table(mov_files, table_columns),
        "",
        "## Files Needing Transcription",
        "",
        markdown_table(transcription_files, table_columns),
        "",
        "## Files Needing Visual Summary",
        "",
        markdown_table(visual_summary_files, table_columns),
        "",
        "## Files Needing Enhancement",
        "",
        markdown_table(enhancement_files, table_columns),
        "",
        "## Likely Archive-Only Files",
        "",
        markdown_table(archive_only, table_columns),
        "",
        "## Likely Content-Gold Files",
        "",
        markdown_table(content_gold, table_columns),
        "",
        "## Next Safe Actions",
        "",
        "- Review the CSV inventory before running any processing.",
        "- Use dry-run conversion, audio extraction, thumbnail, or queue commands first.",
        "- Keep `delete_safe` false until a separate human review policy is created.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_path = Path(args.path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records = scan_folder(source_path, large_file_mb=args.large_file_mb, privacy_level=args.privacy_level)
    queue = build_processing_queue(records)

    csv_output = output_dir / "media_inventory.csv"
    json_output = output_dir / "media_inventory.json"
    queue_output = output_dir / "processing_queue.json"
    report_output = output_dir / "audit_report.md"

    write_inventory_csv(records, csv_output)
    write_inventory_json(records, json_output)
    write_processing_queue(queue, queue_output)
    report_output.write_text(build_audit_report(source_path, output_dir, records, queue), encoding="utf-8")

    print(f"Audited {len(records)} files.")
    print(f"Wrote inventory CSV: {csv_output}")
    print(f"Wrote inventory JSON: {json_output}")
    print(f"Wrote processing queue: {queue_output}")
    print(f"Wrote audit report: {report_output}")
    print("Source files were not moved, renamed, modified, uploaded, or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
