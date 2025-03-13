.PHONY: run debug setup fl lint format clean db-clean up-clean

run:
	uv run gunicorn app:app

debug:
	uv run flask run --reload --debug

fl: format lint

lint:
	uv run ruff check

format:
	uv run prettier -w thehouse/templates/*.html static/*.css
	uv run ruff format

clean:
	rm -rf __pycache__
	rm -rf .venv

db-setup:
	uv run setup_db.py

db-clean: instance
	rm -rf instance

up-clean: uploads
	rm -rf uploads/*
