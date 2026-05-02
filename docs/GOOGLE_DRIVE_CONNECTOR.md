# Google Drive Connector

The first Drive-compatible path is local sync, not API dependency.

## MVP Approach

Use Google Drive for desktop or a manually downloaded Drive folder, then scan the local folder path:

```bash
python3 scripts/scan_media.py --path "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive"
```

Dedicated wrapper:

```bash
python3 scripts/scan_google_drive.py --path "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive"
```

## Connector Goals

- Treat Drive as a source label.
- Preserve local path evidence.
- Avoid requiring API credentials for basic cataloging.
- Support future API metadata only as an optional enrichment layer.

## Future Fields

- `cloud_provider`
- `cloud_file_id`
- `cloud_web_url`
- `cloud_owner`
- `cloud_modified_at`
- `cloud_sync_status`

## Safety Rules

- Do not delete Drive files from the vault.
- Do not move Drive files without explicit approval.
- Do not treat Drive sync state as archive authority.
- Keep local inventory usable even when Drive is offline.
