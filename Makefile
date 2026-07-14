.PHONY: init doctor lint test

init:
	./scripts/init.sh

doctor:
	./scripts/doctor.sh

lint:
	ruff check app tests

test:
	pytest
