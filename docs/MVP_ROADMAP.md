# MVP Roadmap

## MVP 0: Local Inventory

- Accept folder path.
- Recursively scan files.
- Detect video, audio, image, document, and unknown types.
- Extract basic filesystem metadata.
- Flag likely camera or phone media.
- Flag large files.
- Flag MOV conversion candidates.
- Generate CSV inventory.
- Generate JSON inventory.
- Generate processing queue.
- Preserve originals.

## MVP 1: Review Layer

- Prepare ffmpeg conversion commands.
- Prepare MP3 extraction commands.
- Prepare thumbnail generation commands.
- Prepare Whisper transcription commands.
- Prepare local/Kimi summary outputs.
- Keep every transformation opt-in with `--write`.
- Add configurable privacy and content status review.
- Add duplicate candidates.
- Add skip lists.
- Add folder-level source labels.
- Add dry-run reports for proposed moves without moving files.

## MVP 2: Local Enrichment

- Add audio extraction queue.
- Add transcription queue.
- Add image and video summary queue.
- Add sidecar JSON records.
- Add resumable worker status.

## MVP 3: Cloud-Aware Imports

- Support Google Drive synced folders.
- Support Google Takeout folder structure.
- Normalize Google Photos metadata sidecars.
- Track cloud source without requiring cloud API access.
- Prepare Notion and Airtable sync payloads without live writes by default.

## MVP 4: Publishing Prep

- Create curated export sets.
- Generate captions, titles, descriptions, and tags.
- Track rights, privacy, and publish readiness.
- Keep final publishing as explicit user-approved action.
