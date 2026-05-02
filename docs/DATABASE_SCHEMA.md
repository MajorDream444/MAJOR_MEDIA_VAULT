# Database Schema

The MVP writes flat CSV and JSON records. These fields are designed to migrate cleanly into SQLite, Postgres, Airtable, or a vector store later.

## Media Record Fields

| Field | Type | Notes |
| --- | --- | --- |
| `media_id` | string | Stable hash from path, size, and modified time. |
| `original_file_name` | string | Original basename only. |
| `extension` | string | Lowercase extension without dot. |
| `file_type` | string | `video`, `audio`, `image`, `document`, or `unknown`. |
| `mime_type` | string | Guessed MIME type. |
| `file_size_bytes` | integer | Raw byte size. |
| `file_size_mb` | number | Rounded megabytes. |
| `created_at` | string | ISO timestamp from filesystem. |
| `modified_at` | string | ISO timestamp from filesystem. |
| `source_path` | string | Absolute source file path. |
| `parent_folder` | string | Immediate parent folder. |
| `needs_review` | boolean | Review flag. |
| `needs_conversion` | boolean | Conversion flag, especially MOV. |
| `needs_audio_extract` | boolean | Audio extraction flag for video. |
| `needs_transcription` | boolean | Audio/video transcription flag. |
| `needs_visual_summary` | boolean | Image/video summary flag. |
| `needs_thumbnail` | boolean | Video thumbnail flag. |
| `needs_enhancement` | boolean | Enhancement flag. |
| `privacy_level` | string | Default `private`. |
| `content_status` | string | Default `unreviewed`. |
| `archive_status` | string | Default `cataloged`. |
| `delete_safe` | boolean | Always false in MVP. |

## Queue Record Fields

| Field | Type | Notes |
| --- | --- | --- |
| `queue_id` | string | Hash for task identity. |
| `media_id` | string | Linked media record. |
| `task_type` | string | Example: `convert_mov`, `extract_audio`, `transcribe`, `visual_summary`, `review`. |
| `source_path` | string | Original source path. |
| `status` | string | Default `pending`. |
| `priority` | string | Default `normal`. |
| `created_at` | string | Queue creation timestamp. |
| `notes` | string | Human-readable task reason. |

## Current Queue Task Types

| Task Type | Purpose |
| --- | --- |
| `convert_mov` | Convert MOV source to derived MP4. |
| `extract_audio` | Extract derived MP3 audio. |
| `generate_thumbnail` | Create derived review thumbnail. |
| `transcribe` | Generate transcript from audio or video. |
| `visual_summary` | Generate image or video summary. |
| `enhance` | Prepare optional enhancement work. |
| `review` | Require human review before downstream action. |
