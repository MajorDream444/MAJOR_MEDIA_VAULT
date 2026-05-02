# Processing Pipelines

This layer prepares the vault for ffmpeg conversion, MP3 extraction, thumbnail generation, Whisper transcription, local or Kimi summaries, Notion sync, Airtable sync, Google Drive folders, and Google Takeout parsing.

## Local-First Rule

All scripts are safe by default. Media transformation scripts run in dry-run mode unless `--write` is passed. Sync scripts only create local payload files unless live sync is implemented later.

## ffmpeg Workflows

MOV to MP4:

```bash
python3 scripts/convert_mov_to_mp4.py --input "/path/file.MOV"
python3 scripts/convert_mov_to_mp4.py --input "/path/file.MOV" --write
```

MP3 generation:

```bash
python3 scripts/extract_audio_mp3.py --input "/path/file.MOV"
python3 scripts/extract_audio_mp3.py --input "/path/file.MOV" --write
```

Thumbnail generation:

```bash
python3 scripts/generate_thumbnail.py --input "/path/file.MOV"
python3 scripts/generate_thumbnail.py --input "/path/file.MOV" --timestamp 00:00:03 --write
```

## Queue Runner

Run queued tasks in dry-run mode:

```bash
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json --task-type convert_mov
```

Run supported tools for real only after review:

```bash
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json --task-type convert_mov --write
```

## Processed Output Packages

Create per-`media_id` output folders with manifests and notes. Dry-run is the default:

```bash
python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5
```

Write mode only creates derived files under the output directory when dependencies are installed. Originals are never changed or copied.

```bash
python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5 --write
```

## Single Asset Package

Build a complete per-file package with metadata, planned or generated assets, manifest, and notes:

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample
```

Write mode creates derived outputs when dependencies exist and the source is valid:

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample --write
```

Add platform thumbnails and prompt files inside the package:

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample --generate-thumbnails --generate-thumbnail-prompts --thumbnail-preset all
```

Generate platform publishing drafts from an asset package:

```bash
python3 scripts/generate_content_package.py --asset-package-dir exports/asset_package_sample
```

Generate local AI enrichment drafts with Ollama-compatible models:

```bash
python3 scripts/enrich_asset_package.py --asset-package-dir exports/asset_package_sample
python3 scripts/enrich_asset_package.py --asset-package-dir exports/asset_package_sample --write
```

Metadata and sidecar files are read through safe encoding helpers. If a real phone/video metadata file contains non-UTF-8 bytes or invalid JSON, the workflow continues with warning fields instead of crashing.

## Whisper Transcription

Requires the local `whisper` CLI to be installed.

```bash
python3 scripts/transcribe_whisper.py --input "/path/audio.mp3"
python3 scripts/transcribe_whisper.py --input "/path/audio.mp3" --model base --write
```

## Kimi Or Local Model Summaries

The first version writes structured summary placeholders and keeps provider choice explicit.

```bash
python3 scripts/summarize_media.py --input exports/transcripts/example.json --provider local
python3 scripts/summarize_media.py --input exports/transcripts/example.json --provider kimi
```

## Notion And Airtable Sync

Current behavior writes dry-run payloads:

```bash
python3 scripts/sync_notion.py --inventory data/media_inventory.json
python3 scripts/sync_airtable.py --inventory data/media_inventory.json
```

Future live write mode must require explicit credentials and should never print secrets.

## Google Drive Connector

The first connector scans the local Google Drive folder created by Google Drive for desktop.

```bash
python3 scripts/scan_google_drive.py --path "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive"
```

## Google Takeout Parser

The parser scans the Takeout folder and creates a sidecar map for Google JSON metadata.

```bash
python3 scripts/parse_google_takeout.py --path "/path/to/Takeout"
```
