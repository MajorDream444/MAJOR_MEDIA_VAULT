.PHONY: scan-sample audit-sample process-sample-dry-run package-sample thumbnails-sample thumbnail-prompts-sample content-package-sample enrich-sample check-deps test-compile

scan-sample:
	python3 scripts/scan_media.py --path examples/sample_media --output data/media_inventory.csv

audit-sample:
	python3 scripts/run_media_audit.py --path examples/sample_media --output-dir exports/sample_audit

process-sample-dry-run:
	python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5

package-sample:
	python3 scripts/build_asset_package.py --input examples/sample_media/DCIM/VID_0002.MOV --output-dir exports/asset_package_sample

thumbnails-sample:
	python3 scripts/generate_platform_thumbnails.py --input examples/sample_media/DCIM/IMG_0001.JPG --output-dir exports/thumbnail_sample

thumbnail-prompts-sample:
	python3 scripts/generate_thumbnail_prompts.py --asset-package-dir exports/asset_package_sample

content-package-sample:
	python3 scripts/generate_content_package.py --asset-package-dir exports/asset_package_sample

enrich-sample:
	python3 scripts/enrich_asset_package.py --asset-package-dir exports/asset_package_sample

check-deps:
	python3 scripts/check_dependencies.py

test-compile:
	python3 -m compileall scripts src
