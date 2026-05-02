#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.media_vault.workflows import (  # noqa: E402
    convert_mov_to_mp4,
    extract_audio_mp3,
    generate_thumbnail,
    summarize_with_local_model,
    transcribe_with_whisper,
    write_json,
)


def load_queue(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as queue_file:
        data = json.load(queue_file)
    if not isinstance(data, list):
        raise ValueError("Queue JSON must be a list of task records.")
    return data


def run_task(task: dict[str, object], dry_run: bool) -> dict[str, object]:
    task_type = str(task.get("task_type", ""))
    source_path = Path(str(task["source_path"]))

    if task_type == "convert_mov":
        result = convert_mov_to_mp4(source_path, Path("exports/conversions"), dry_run=dry_run)
    elif task_type == "extract_audio":
        result = extract_audio_mp3(source_path, Path("exports/audio"), dry_run=dry_run)
    elif task_type == "generate_thumbnail":
        result = generate_thumbnail(source_path, Path("exports/thumbnails"), dry_run=dry_run)
    elif task_type == "transcribe":
        result = transcribe_with_whisper(source_path, Path("exports/transcripts"), dry_run=dry_run)
    elif task_type == "visual_summary":
        result = summarize_with_local_model(source_path, Path("exports/summaries"), provider="local", model="local", dry_run=dry_run)
    else:
        result = {"status": "skipped", "reason": f"No runner implemented for task_type={task_type}"}

    return {
        "queue_id": task.get("queue_id"),
        "media_id": task.get("media_id"),
        "task_type": task_type,
        "source_path": str(source_path),
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run selected processing queue tasks. Default is dry-run.")
    parser.add_argument("--queue", default="queues/processing_queue.json", help="Queue JSON path.")
    parser.add_argument("--task-type", action="append", help="Only run matching task type. Can be passed multiple times.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks. 0 means no limit.")
    parser.add_argument("--output", default="exports/queue_run_report.json", help="Run report output path.")
    parser.add_argument("--write", action="store_true", help="Actually run supported tools. Default is dry-run.")
    args = parser.parse_args()

    queue = load_queue(Path(args.queue))
    selected = [task for task in queue if not args.task_type or task.get("task_type") in set(args.task_type)]
    if args.limit:
        selected = selected[: args.limit]

    report = [run_task(task, dry_run=not args.write) for task in selected]
    write_json(report, Path(args.output))
    print(f"Processed {len(report)} queued tasks. Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
