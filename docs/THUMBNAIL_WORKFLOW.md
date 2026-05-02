# Thumbnail Workflow

MAJOR_MEDIA_VAULT supports two artwork layers:

- Local utility thumbnails generated from source images or video frames.
- AI-designed thumbnail prompt files for higher-end generated designs.

All artwork is derived output only. Originals are never moved, renamed, modified, uploaded, or deleted.

## Platform Sizes

| Preset | Platform | Size | Use |
| --- | --- | --- | --- |
| `youtube_16x9` | YouTube | 1280x720 | Video thumbnail and widescreen preview. |
| `vertical_9x16` | TikTok, Reels, Shorts | 1080x1920 | Vertical cover. |
| `square_1x1` | Instagram, LinkedIn, X | 1080x1080 | Square feed artwork. |
| `feed_4x5` | Instagram, LinkedIn | 1080x1350 | Tall feed post. |
| `story_9x16` | Stories, TikTok, Reels | 1080x1920 | Story frame and mobile cover. |
| `substack_header` | Substack | 1600x900 | Newsletter header and essay hero. |
| `podcast_cover` | Podcast directories | 3000x3000 | Podcast cover art. |

Preset details live in `config/thumbnail_presets.json`.

The saved premium YouTube design template lives at:

```text
config/design_templates/youtube_thumbnail_premium.md
```

## Local Utility Thumbnails

Dry-run:

```bash
python3 scripts/generate_platform_thumbnails.py --input examples/sample_media/DCIM/IMG_0001.JPG --output-dir exports/thumbnail_sample
```

Write derived JPGs:

```bash
python3 scripts/generate_platform_thumbnails.py --input examples/sample_media/DCIM/IMG_0001.JPG --output-dir exports/thumbnail_sample --write
```

Generate one preset:

```bash
python3 scripts/generate_platform_thumbnails.py --input examples/sample_media/DCIM/IMG_0001.JPG --output-dir exports/thumbnail_sample --preset youtube_16x9 --write
```

## Asset Package Thumbnails

```bash
python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample --generate-thumbnails --thumbnail-preset all
```

Outputs land under:

```text
asset_package/thumbnails/
```

## AI Thumbnail Prompts

Prompt generation reads `summary.md`, `transcript.txt`, `metadata.json`, and `asset_manifest.json` when present.

```bash
python3 scripts/generate_thumbnail_prompts.py --asset-package-dir exports/asset_package_sample
```

Outputs:

- `prompts/youtube_thumbnail_prompt.md`
- `prompts/vertical_cover_prompt.md`
- `prompts/square_cover_prompt.md`
- `prompts/substack_header_prompt.md`
- `prompts/podcast_cover_prompt.md`

Each prompt includes platform, exact aspect ratio, visual concept, headline text, emotional tone, subject description, background style, readable text guidance, no-clutter direction, and a premium creator/founder documentary look.

## Platform Usage

- YouTube: use `youtube_16x9.jpg` or `youtube_thumbnail_prompt.md`.
- TikTok/Reels/Shorts: use `vertical_9x16.jpg`, `story_9x16.jpg`, or `vertical_cover_prompt.md`.
- Instagram feed: use `square_1x1.jpg`, `feed_4x5.jpg`, or `square_cover_prompt.md`.
- Substack: use `substack_header.jpg` or `substack_header_prompt.md`.
- Podcast covers: use `podcast_cover.jpg` or `podcast_cover_prompt.md`.
