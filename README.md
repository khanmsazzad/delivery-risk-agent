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

'''bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -v'''

## Local AI agent 

The agent uses the OpenAI Agents SDK for orchestration and a local
Qwen model served through llama.cpp's OpenAI-compatible API.

Start the local model server:

'''bash
llama-server \
  -hf lmstudio-community/Qwen2.5-7B-Instruct-GGUF:Q4_K_M \
  --alias qwen-local \
  --jinja \
  -ngl 0 \
  --port 8080
,,,

In another terminal, run the agent:

'''bash
python -m delivery_risk_agent.agent data/sample_project.json
'''

No OpenAI API key is required when using the local model.