VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip3
FLASK = $(VENV)/bin/flask
GUNICORN = $(VENV)/bin/gunicorn

AUTOPEP8 = $(VENV)/bin/autopep8
PYLINT = $(VENV)/bin/pylint
ISORT = $(VENV)/bin/isort

.PHONY: run lint format fl clean

run:
	$(GUNICORN) app:app

debug:
	$(FLASK) run --reload --debug

setup: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	mkdir -p uploads/

fl: format lint

lint:
	$(PYLINT) -f colorized *.py

format:
	prettier -w templates/*.html
	$(ISORT) *.py
	$(AUTOPEP8) -i *.py

clean:
	rm -rf __pycache__
	rm -rf $(VENV)

db-setup:
	$(PYTHON) setup_db.py

db-clean: instance
	rm -rf instance

up-clean: uploads
	rm -rf uploads/*
