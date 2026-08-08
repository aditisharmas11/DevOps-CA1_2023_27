VENV   ?= .venv
PYTHON ?= python3.11
PY     ?= $(VENV)/bin/python
CONFIG ?= config/default.yaml
IMAGE  ?= smartphone-addiction-s6e8

.PHONY: setup inspect eda train predict all test lint fmt docker-build docker-run clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

inspect:
	$(PY) -m src.cli inspect --config $(CONFIG)

eda:
	PYTHONPATH=. $(PY) scripts/make_eda.py --config $(CONFIG)

train:
	$(PY) -m src.cli train --config $(CONFIG)

predict:
	$(PY) -m src.cli predict --config $(CONFIG)

all: inspect train predict

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

fmt:
	$(PY) -m ruff format .

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD)/data:/app/data" \
		-v "$(PWD)/models:/app/models" \
		-v "$(PWD)/reports:/app/reports" \
		-v "$(PWD)/submissions:/app/submissions" \
		$(IMAGE)

clean:
	rm -f models/*.pkl models/*.json
	rm -f reports/figures/*.png
	rm -f reports/metrics.json reports/oof_predictions.csv
	rm -f submissions/*.csv
	find data/processed -type f ! -name '.gitkeep' -delete
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
