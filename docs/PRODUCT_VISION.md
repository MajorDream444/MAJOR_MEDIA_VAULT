# Product Vision

MAJOR_MEDIA_VAULT is a private media intelligence layer for creators, operators, and archives with large bodies of photos, videos, audio, documents, downloads, and drive exports.

The system turns local folders, external drives, Google Drive folders, and later Google Photos or Google Takeout exports into structured, searchable records. It is designed to protect original files while preparing them for AI-assisted enrichment, transcription, enhancement, and publishing workflows.

## Product Promise

Every file becomes searchable IP without forcing the user to surrender custody of the archive.

## Operating Principles

- Originals are preserved.
- Classification happens before movement or publishing.
- Local filesystem scanning works before any cloud dependency.
- Cloud sources are treated as inputs, not authorities.
- Bulk processing should be cheap, resumable, and auditable.
- Premium model work should be reserved for high-value media.
- Deletion requires explicit downstream review and is never a first action.

## First User Journey

1. User points the vault at a folder.
2. The vault scans recursively.
3. The vault classifies files by media type.
4. The vault writes inventory records.
5. The vault creates processing queue tasks.
6. The user reviews what exists before any future move, conversion, upload, or publishing action.
