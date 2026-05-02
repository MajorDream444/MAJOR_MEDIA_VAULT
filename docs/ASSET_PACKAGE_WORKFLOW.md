# Asset Package Workflow

The asset package workflow creates a per-file review package under `exports/` while preserving the original source file.

## Safety Rules

- Originals are never moved.
- Originals are never renamed.
- Originals are never modified.
- Originals are never uploaded.
- Originals are never deleted.
- Originals are not copied unless `--copy-original` is passed.

Every manifest includes:

```text
Original was not moved, renamed, modified, uploaded, or deleted.
```

## Dry-Run Package

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample
```

Dry-run mode creates package metadata, notes, manifests, and planned commands without generating derived media.

## Write Package

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample --write
```

Write mode creates any possible derived outputs when dependencies are installed and the source file is valid. If a dependency is missing or a media tool cannot process the source, the package records the failure instead of crashing.

## Optional Original Copy

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample --write --copy-original
```

Use this only when you explicitly want a copied source inside the package. The original file still remains untouched.

## Package Contents

Each package folder is named by stable `media_id` and can contain:

- `metadata.json`
- `thumbnail.jpg`
- `audio.mp3`
- `converted.mp4`
- `transcript.txt`
- `summary.md`
- `asset_manifest.json`
- `asset_notes.md`

The sample placeholder MOV may not produce real derived media even when `ffmpeg` is installed, because it is not a real video file. In that case, `asset_manifest.json` records `failed` statuses with command stderr.
