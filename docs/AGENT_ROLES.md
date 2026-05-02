# Agent Roles

MAJOR_MEDIA_VAULT is designed for multiple narrow agents over time.

## Scanner Agent

Builds inventory records from local files. It is read-only against source media.

## Metadata Agent

Extracts filesystem, MIME, EXIF, media duration, codec, and sidecar metadata.

## Conversion Agent

Uses ffmpeg to create derived MP4 files from MOV originals. It writes outputs under `exports/` and never replaces source files.

## Audio Agent

Uses ffmpeg to extract MP3 audio from video or audio originals for downstream transcription.

## Thumbnail Agent

Uses ffmpeg to create visual review thumbnails for video records.

## Queue Agent

Creates processing tasks from inventory records and keeps future workers resumable.

## Transcription Agent

Processes audio and video tasks that require text transcripts, starting with local Whisper.

## Visual Summary Agent

Creates structured summaries for images and videos using local or explicitly approved premium models.

## Enhancement Agent

Prepares optional upscale, cleanup, audio leveling, or conversion tasks.

## Publishing Agent

Builds captions, titles, descriptions, tags, and export packages only after privacy and rights review.

## Review Agent

Applies human-facing review states. It should never mark deletion safe without explicit user policy.

## Sync Agent

Prepares Notion and Airtable payloads. Live sync requires explicit credentials and explicit write mode.

## Connector Agent

Handles Google Drive local folder scans and Google Takeout parsing before any cloud API dependency is introduced.
