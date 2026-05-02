# Operator Quickstart

MAJOR_MEDIA_VAULT is local-first and read-only against source media by default.

## Scan Sample Folder

```bash
python3 scripts/scan_media.py --path examples/sample_media --output data/media_inventory.csv
```

## Run Full Audit

```bash
python3 scripts/run_media_audit.py --path examples/sample_media --output-dir exports/sample_audit
```

This creates:

- `exports/sample_audit/media_inventory.csv`
- `exports/sample_audit/media_inventory.json`
- `exports/sample_audit/processing_queue.json`
- `exports/sample_audit/audit_report.md`

## Run Dry-Run Conversion

```bash
python3 scripts/convert_mov_to_mp4.py --input examples/sample_media/DCIM/VID_0002.MOV
```

## Run Dry-Run Audio Extraction

```bash
python3 scripts/extract_audio_mp3.py --input examples/sample_media/DCIM/VID_0002.MOV
```

## Run Dry-Run Thumbnail Generation

```bash
python3 scripts/generate_thumbnail.py --input examples/sample_media/DCIM/VID_0002.MOV
```

## Run Queue Dispatcher Dry-Run

```bash
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json
```

For a specific task type:

```bash
python3 scripts/run_processing_queue.py --queue queues/processing_queue.json --task-type convert_mov
```

## Run Processed Output Dry-Run

```bash
python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5
```

Run write mode after review. This still never modifies originals; it only creates derived outputs when dependencies are installed.

```bash
python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5 --write
```

## Check Dependencies

```bash
python3 scripts/check_dependencies.py
```

## Make Commands

```bash
make scan-sample
make audit-sample
make process-sample-dry-run
make check-deps
make test-compile
```
