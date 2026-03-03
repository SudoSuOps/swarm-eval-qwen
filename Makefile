.PHONY: validate eval eval-baseline regression release-pack clean help

MODEL ?= swarmjudge-9b-cre-b0
PHASE ?= phase2

help:
	@echo "swarm-eval-qwen"
	@echo ""
	@echo "  make validate     MODEL=... PHASE=...  Schema + leak checks"
	@echo "  make eval         MODEL=... PHASE=...  Run eval suites"
	@echo "  make eval-baseline MODEL=... PHASE=... Run Phase N-1 baseline"
	@echo "  make regression   MODEL=... PHASE=...  Regression gate"
	@echo "  make release-pack MODEL=... PHASE=...  Bundle release artifacts"
	@echo "  make clean                              Remove temp files"

validate:
	bash scripts/02_validate_data.sh $(MODEL) $(PHASE)

eval:
	bash scripts/05_eval.sh $(MODEL) $(PHASE)

eval-baseline:
	bash scripts/05_eval.sh $(MODEL) $(PHASE) --baseline

regression:
	bash scripts/06_regression_gate.sh $(MODEL) $(PHASE)

release-pack:
	bash scripts/07_release_pack.sh $(MODEL) $(PHASE)

clean:
	find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
