# Engineering Delivery Risk Agent

An agentic workflow that identifies software delivery risks from project snapshots and public GitHub pull requests.

Python rules detect risks and assign severity. A local AI advisor explains their potential delivery impact and recommends actions. The final assessment preserves the findings and severity determined by the rules.

## Current capabilities

- Validates project snapshots with Pydantic
- Detects blocked critical work
- Detects unassigned high-priority work
- Detects pull requests with failing CI
- Reads open pull requests and check runs from public GitHub repositories
- Includes synthetic sample data and automated tests

## How the workflow works

1. Load a JSON snapshot or build one from GitHub PR data.
2. Run deterministic Python rules to detect risks.
3. Send the findings to a local advisor agent for impact analysis and recommended actions.
4. Check that the agent addressed every finding.
5. Build the final assessment using the original severity and evidence.

The agent can advise on a risk, but it cannot change the severity assigned by the Python rules.

## Run locally

Create a virtual environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the deterministic report without starting a model:

```bash
python -m delivery_risk_agent.report data/sample_project.json
```

## Run the local AI advisor

The advisor uses the OpenAI Agents SDK and a local Qwen model served through llama.cpp's OpenAI-compatible API.

Start the model server in one terminal:

```bash
llama-server \
  -hf lmstudio-community/Qwen2.5-7B-Instruct-GGUF:Q4_K_M \
  --alias qwen-local \
  --jinja \
  -ngl 0 \
  --port 8080
```

In another terminal, activate the virtual environment and run:

```bash
python -m delivery_risk_agent.agent data/sample_project.json
```

The local setup does not require an OpenAI API key.

## Analyze public GitHub pull requests

Inspect open PRs and their check runs:

```bash
python -m delivery_risk_agent.github_reader fastapi fastapi
```

Build a snapshot from GitHub and run the advisor:

```bash
python -m delivery_risk_agent.github_snapshot fastapi fastapi
```

The arguments are the GitHub repository owner and name. For example, [`fastapi/fastapi`](https://github.com/fastapi/fastapi) becomes `fastapi fastapi`.

The GitHub workflow is read-only. It does not modify PRs or repository settings.

## Run checks

Run the ordinary tests and lint check:

```bash
pytest -v
ruff check .
```

To run the live agent integration test, start llama.cpp first and then run:

```bash
RUN_AGENT_TESTS=1 pytest -v -m integration
```

## Current scope

- The GitHub reader examines the first five open PRs; pagination is not implemented yet.
- It reads GitHub check runs. Pending or unknown results are not treated as failed CI.
- GitHub review status and links to work items are not fetched yet.
- Impact explanations and actions are AI-generated suggestions for a person to review. Python rules remain the source of truth for detected risks, severity, and evidence.