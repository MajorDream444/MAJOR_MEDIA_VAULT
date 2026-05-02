# Privacy And IP Rules

MAJOR_MEDIA_VAULT exists to make media more usable while protecting original assets and private context.

## Default Privacy Posture

- New records default to `privacy_level = private`.
- New records default to `content_status = unreviewed`.
- New records default to `delete_safe = false`.
- No generated workflow should publish, upload, delete, or share media by default.

## IP Rules

- Preserve source path evidence.
- Preserve original filenames.
- Prefer sidecar metadata over destructive edits.
- Track every transformation as a new output, not a replacement.
- Keep publishing readiness separate from cataloging.

## Human Review Required

Human review is required before:

- Deletion.
- Public publishing.
- Cloud upload.
- Face/name tagging.
- Sensitive document processing.
- Rights-sensitive commercial use.

## Model Use

- Cheap local or low-cost models should handle bulk classification and summaries.
- Premium models should be reserved for selected high-value records.
- Private or sensitive records should stay local unless explicitly approved for cloud processing.
