# Engineering Delivery Risk Agent

An agentic workflow for identifying software delivery risks from project and repository data.

## Current capabilities

- Validates project data using Pydantic
- Detects blocked critical work
- Detects unassigned high-priority work
- Detects pull requests with failing CI
- Includes automated tests and synthetic sample data

## Project status

This project is under active development. The current version provides a deterministic
risk-analysis baseline. Future versions will add GitHub integration, AI agents,
critique and validation, human approval, and a dashboard.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -v