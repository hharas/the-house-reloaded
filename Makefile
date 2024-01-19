VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/python3 -m pip
FLASK = $(VENV)/bin/flask
GUNICORN = $(VENV)/bin/gunicorn

AUTOPEP8 = $(VENV)/bin/autopep8
PYLINT = $(VENV)/bin/pylint
ISORT = $(VENV)/bin/isort

.PHONY: run debug setup fl lint format clean db-clean up-clean

run:
	$(GUNICORN) app:app

debug:
	$(FLASK) run --reload --debug

setup: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

fl: format lint

lint:
	$(PYLINT) -f colorized *.py thehouse/*.py

format:
	prettier -w thehouse/templates/*.html static/*.css
	$(ISORT) *.py thehouse/*.py
	$(AUTOPEP8) -i *.py thehouse/*.py

clean:
	rm -rf __pycache__
	rm -rf $(VENV)

db-setup:
	$(PYTHON) setup_db.py

db-clean: instance
	rm -rf instance

up-clean: uploads
	rm -rf uploads/*
