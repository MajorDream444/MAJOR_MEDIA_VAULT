# Content Package Workflow

The content package workflow turns an asset package into deterministic, platform-ready publishing drafts.

It does not call an AI model yet. It uses local templates and whatever package context exists: `metadata.json`, `summary.md`, `transcript.txt`, `asset_manifest.json`, `asset_notes.md`, and prompt files under `prompts/`.

## Safety

- Originals are never moved.
- Originals are never renamed.
- Originals are never modified.
- Originals are never uploaded.
- Originals are never deleted.
- Drafts are derived output only.
- Human review is required before publishing.

## Command

```bash
python3 scripts/generate_content_package.py --asset-package-dir exports/asset_package_sample
```

By default, output is written to:

```text
asset_package/content_package/
```

Use a custom output directory:

```bash
python3 scripts/generate_content_package.py --asset-package-dir exports/asset_package_sample --output-dir exports/content_package_sample
```

## Generated Folders

- `youtube/`
- `tiktok_reels/`
- `substack/`
- `podcast/`
- `agent_memory/`

## Generated Files

- `youtube/title_options.md`
- `youtube/description.md`
- `youtube/tags.txt`
- `youtube/thumbnail_prompt.md`
- `youtube/chapters.md`
- `tiktok_reels/hook_options.md`
- `tiktok_reels/caption_options.md`
- `tiktok_reels/cover_prompt.md`
- `tiktok_reels/hashtags.txt`
- `substack/essay_seed.md`
- `substack/headline_options.md`
- `substack/intro.md`
- `substack/pull_quotes.md`
- `podcast/episode_title_options.md`
- `podcast/show_notes.md`
- `podcast/description.md`
- `agent_memory/memory_card.md`
- `agent_memory/doctrine_notes.md`
- `agent_memory/reusable_quotes.md`
- `content_package_manifest.json`

## Placeholder Behavior

If `transcript.txt` or `summary.md` is missing, the generated drafts include clear placeholder notes. This keeps the workflow usable while making review gaps visible.
