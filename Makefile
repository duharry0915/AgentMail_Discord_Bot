# AgentMail Discord Bot - Convenience targets
PY = .venv/bin/python

.PHONY: install ingest run export

install:
	$(PY) -m pip install -r requirements.txt

ingest:
	$(PY) ingest_hyperspell.py

run:
	$(PY) main.py

export:
	$(PY) export_support.py
