# MAJOR_MEDIA_VAULT

MAJOR_MEDIA_VAULT is a local-first AI media intelligence engine for turning scattered files into searchable IP without risking originals.

The first version scans a folder, classifies media files, extracts basic filesystem metadata, flags files for future workflows, and writes inventory plus queue artifacts.

## Core Rules

- Never delete first.
- Preserve originals.
- Classify before moving.
- Local-first by default.
- Cloud-aware but not cloud-dependent.
- Cheap models for long-running bulk work.
- Premium models only for high-value enrichment.
- Every file becomes searchable IP.

## Quick Start

```bash
python3 scripts/scan_media.py --path "/path/to/folder" --output data/media_inventory.csv
```

This writes:

- `data/media_inventory.csv`
- `data/media_inventory.json`
- `queues/processing_queue.json`

No files are moved, renamed, edited, uploaded, or deleted.

## Repo Layout

```text
docs/      Product, architecture, workflow, schema, and policy docs
scripts/   CLI entrypoints for scanning, metadata, inventory, and queue creation
src/       Shared Python engine code
config/    Future runtime configuration
data/      Local generated inventory outputs
queues/    Local generated processing queues
exports/   Future publish/export bundles
examples/  Sample inputs and sample output files
```

## Main CLI

```bash
python3 scripts/scan_media.py \
  --path "/path/to/folder" \
  --output data/media_inventory.csv \
  --json-output data/media_inventory.json \
  --queue-output queues/processing_queue.json
```

Optional flags:

- `--large-file-mb 100` sets the large-file threshold.
- `--privacy-level private` sets the default privacy classification.

## Processing CLIs

These scripts are prepared for the next workflow layer. Transform scripts are dry-run by default and require `--write` before creating derived files.

```bash
python3 scripts/convert_mov_to_mp4.py --input "/path/file.MOV"
python3 scripts/extract_audio_mp3.py --input "/path/file.MOV"
python3 scripts/generate_thumbnail.py --input "/path/file.MOV"
python3 scripts/transcribe_whisper.py --input "/path/audio.mp3"
python3 scripts/summarize_media.py --input exports/transcripts/example.json --provider local
python3 scripts/sync_notion.py --inventory data/media_inventory.json
python3 scripts/sync_airtable.py --inventory data/media_inventory.json
python3 scripts/scan_google_drive.py --path "/path/to/local/Google Drive"
python3 scripts/parse_google_takeout.py --path "/path/to/Takeout"
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json --task-type convert_mov
python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5
```

See [docs/PROCESSING_PIPELINES.md](/Users/majordreamwilliams/Documents/New%20project%208/docs/PROCESSING_PIPELINES.md).

## Current Status

MVP v0 is a read-only local scanner plus safe workflow scaffolding. ffmpeg, Whisper, model summaries, Notion, Airtable, Google Drive, and Google Takeout paths are explicit, local-first, and guarded from accidental writes.
