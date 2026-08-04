.PHONY: init doctor lint test seiton-init

init:
	./scripts/init.sh

seiton-init:
	./scripts/seiton init

doctor:
	./scripts/doctor.sh

lint:
	ruff check app tests

test:
	pytest
