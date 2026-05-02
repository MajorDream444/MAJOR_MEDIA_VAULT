# System Architecture

MAJOR_MEDIA_VAULT starts as a local Python engine with a clear path toward connectors and enrichment workers.

## Current Components

- `scripts/scan_media.py`: primary CLI scanner.
- `scripts/extract_metadata.py`: single-file or folder metadata extractor.
- `scripts/generate_inventory.py`: inventory-focused wrapper.
- `scripts/create_processing_queue.py`: queue builder from inventory JSON.
- `scripts/convert_mov_to_mp4.py`: ffmpeg MOV to MP4 command wrapper.
- `scripts/extract_audio_mp3.py`: ffmpeg MP3 extraction wrapper.
- `scripts/generate_thumbnail.py`: ffmpeg thumbnail wrapper.
- `scripts/transcribe_whisper.py`: local Whisper CLI wrapper.
- `scripts/summarize_media.py`: local/Kimi summary placeholder generator.
- `scripts/sync_notion.py`: Notion sync payload preparer.
- `scripts/sync_airtable.py`: Airtable sync payload preparer.
- `scripts/scan_google_drive.py`: local Google Drive folder scanner.
- `scripts/parse_google_takeout.py`: Takeout folder scanner and sidecar mapper.
- `scripts/run_processing_queue.py`: dry-run-first queue dispatcher.
- `src/media_vault/inventory.py`: shared scanning, classification, serialization, and queue logic.
- `src/media_vault/workflows.py`: shared workflow command helpers.
- `data/`: local inventory outputs.
- `queues/`: local processing queues.
- `examples/`: sample input and output artifacts.

## Data Flow

```text
folder path
  -> recursive scanner
  -> file classifier
  -> metadata extractor
  -> inventory CSV/JSON
  -> processing queue JSON
  -> dry-run workflow commands
  -> derived exports only after explicit --write
```

## Future Components

- Queue runner that can execute selected task types.
- Real Notion and Airtable writes after approval and credentials.
- Optional Google Drive API metadata enrichment.
- Google Photos sidecar normalization.
- Duplicate and near-duplicate review.
- Publishing/export bundles.

## Safety Boundary

The scanner is read-only against source media. It only writes inventory and queue artifacts inside the repo unless the user provides another output path.
