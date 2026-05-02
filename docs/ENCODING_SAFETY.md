# Encoding Safety

Media metadata is not always clean UTF-8 text.

Phone videos, EXIF blocks, ffprobe output, external-drive sidecars, copied files, and older exports can contain byte sequences from different encodings or corrupted metadata fields. If those bytes are read as strict UTF-8, Python can raise `UnicodeDecodeError` before the vault has a chance to continue.

## Vault Policy

MAJOR_MEDIA_VAULT treats metadata as untrusted input.

- Originals are never modified.
- Metadata reads should degrade gracefully.
- Generated JSON is always written as UTF-8.
- If JSON cannot be parsed, workflows keep running with a warning object.
- If text cannot be decoded cleanly, undecodable bytes are replaced.

## Shared Helpers

Safe IO lives in:

```text
src/media_vault/io_utils.py
```

Helpers:

- `read_text_safe(path)`: tries `utf-8`, `utf-8-sig`, `latin-1`, then byte decoding with replacement.
- `read_json_safe(path)`: reads via `read_text_safe`; returns a warning object if JSON parsing fails.
- `write_text_safe(path, content)`: writes UTF-8 text.
- `write_json_safe(path, data)`: writes UTF-8 JSON with `ensure_ascii=False`.
- `sanitize_for_json(value)`: recursively sanitizes strings, bytes, dicts, lists, and scalar values.

## Degraded Context

When bad metadata is encountered, downstream packages include warnings such as:

```json
{
  "_read_error": "JSON parse failed: ...",
  "_source_path": "...",
  "_raw_preview": "..."
}
```

Content and enrichment generation should continue with degraded context and human-review warnings instead of crashing.
