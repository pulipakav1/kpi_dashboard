PYTHON  = python
PIP     = $(PYTHON) -m pip
DBT     = dbt
PSQL    = psql

.DEFAULT_GOAL := help

.PHONY: help install install-dev generate setup-db dbt-run dbt-test dbt-docs lint test clean

help:
	@echo "SaaS KPI Dashboard"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "  install      Install runtime dependencies"
	@echo "  install-dev  Install all dependencies including dbt, sqlfluff, dev tools"
	@echo "  generate     Generate synthetic SaaS dataset (CSVs)"
	@echo "  setup-db     Load CSVs into PostgreSQL (requires DB running)"
	@echo "  dbt-run      Run all dbt models (staging + marts)"
	@echo "  dbt-test     Run dbt schema tests"
	@echo "  dbt-docs     Generate and serve dbt docs"
	@echo "  lint         Run ruff (Python) + sqlfluff (SQL) linting"
	@echo "  test         Run pytest suite"
	@echo "  clean        Remove generated CSV files and dbt artifacts"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

generate:
	$(PYTHON) generate_saas_data.py

setup-db:
	$(PSQL) "$(DATABASE_URL)" -f db_setup.sql

dbt-run:
	cd dbt && $(DBT) run

dbt-test:
	cd dbt && $(DBT) test

dbt-docs:
	cd dbt && $(DBT) docs generate && $(DBT) docs serve

lint:
	ruff check generate_saas_data.py tests/
	sqlfluff lint dbt/models/ --dialect postgres

test:
	pytest tests/ -v --cov=. --cov-report=term-missing

clean:
	rm -f customers.csv subscriptions.csv payments.csv costs.csv
	rm -rf dbt/target/ dbt/dbt_packages/ dbt/logs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
