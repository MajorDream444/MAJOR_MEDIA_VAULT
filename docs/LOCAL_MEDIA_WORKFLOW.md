# Local Media Workflow

## Safe First Pass

1. Choose a source folder.
2. Run the scanner.
3. Review `data/media_inventory.csv`.
4. Review `queues/processing_queue.json`.
5. Decide which future workflows should run.

## Command

```bash
python3 scripts/scan_media.py --path "/path/to/folder" --output data/media_inventory.csv
```

## What The Scanner Does

- Reads folder contents recursively.
- Detects media type from extension and MIME type.
- Extracts size and timestamps.
- Creates stable `media_id` values.
- Adds workflow status fields.
- Writes local inventory and queue files.

## What The Scanner Does Not Do

- It does not delete files.
- It does not move files.
- It does not rename files.
- It does not upload files.
- It does not modify source media.

## Review Signals

- `needs_review`: true when a file is unknown, unusually large, or has unclear processing needs.
- `needs_conversion`: true for MOV files.
- `needs_audio_extract`: true for video files.
- `needs_transcription`: true for audio and video files.
- `needs_visual_summary`: true for image and video files.
- `needs_thumbnail`: true for video files.
- `needs_enhancement`: false by default until a review or enrichment pass requests it.
- `delete_safe`: always false in the first pass.

## Optional Workflow Prep

After review, derived outputs can be created under `exports/`:

- MP4 conversions in `exports/conversions/`.
- MP3 audio in `exports/audio/`.
- Thumbnails in `exports/thumbnails/`.
- Transcripts in `exports/transcripts/`.
- Summaries in `exports/summaries/`.

Each processing script defaults to dry-run mode and requires `--write` for actual derived file generation.
