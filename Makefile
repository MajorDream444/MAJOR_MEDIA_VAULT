.PHONY: scan-sample audit-sample process-sample-dry-run check-deps test-compile

scan-sample:
	python3 scripts/scan_media.py --path examples/sample_media --output data/media_inventory.csv

audit-sample:
	python3 scripts/run_media_audit.py --path examples/sample_media --output-dir exports/sample_audit

process-sample-dry-run:
	python3 scripts/process_selected_media.py --queue exports/sample_audit/processing_queue.json --output-dir exports/processed_sample --limit 5

check-deps:
	python3 scripts/check_dependencies.py

test-compile:
	python3 -m compileall scripts src
