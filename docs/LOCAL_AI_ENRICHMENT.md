# Local AI Enrichment

The local AI enrichment workflow uses Ollama-compatible models to generate derived text from an asset package.

It reads package context only:

- `metadata.json`
- `transcript.txt`
- `summary.md`
- `asset_notes.md`
- `asset_manifest.json`
- `prompts/*.md`

It never modifies originals.

## Model Config

Local model preferences live in:

```text
config/local_models.json
```

Default:

```json
{
  "default_model": "kimi",
  "fallback_model": "llama3.2",
  "tasks": {
    "summary": "kimi",
    "seo": "kimi",
    "agent_memory": "kimi"
  }
}
```

## Dry-Run

```bash
python3 scripts/enrich_asset_package.py --asset-package-dir exports/asset_package_sample
```

Dry-run creates placeholder enrichment files and an `enrichment_manifest.json` without calling Ollama.

## Write Mode

```bash
python3 scripts/enrich_asset_package.py --asset-package-dir exports/asset_package_sample --write
```

Write mode calls:

```bash
ollama run MODEL PROMPT
```

If Ollama or the selected model is unavailable, the workflow writes clear skipped files instead of failing the package.

## Outputs

Generated under `asset_package/enrichment/`:

- `visual_summary.md`
- `narrative_summary.md`
- `seo_tags.md`
- `title_options.md`
- `clip_ideas.md`
- `substack_angles.md`
- `agent_memory_enriched.md`
- `privacy_review.md`
- `enrichment_manifest.json`

## Low Context

If `transcript.txt` is missing, outputs are marked `low_context`. Those drafts should be treated as metadata-driven placeholders until transcription exists.

## Review Rule

All enrichment output is derived text only. Human review is required before publishing.
