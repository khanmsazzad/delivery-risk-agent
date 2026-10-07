# Engineering Delivery Risk Agent

A local dashboard that analyzes delivery risks from public GitHub pull
requests and Jira Cloud issues.

Python rules detect risks and assign severity. A local AI advisor explains
potential delivery impact and recommends actions. Python preserves the
original findings, severity, and evidence in the final assessment.

## What it analyzes

- GitHub: failing CI in the first five open pull requests.
- Jira: unassigned, unfinished high-priority work in an accessible project.
- JSON snapshots: blocked critical work, unassigned high-priority work,
  and failing CI.

GitHub and Jira have separate dashboard panels, with independent results,
loading messages, and errors.

## Requirements

- Python 3.11 or newer
- Node.js 22.12 or newer, with npm
- Git
- llama.cpp with the `llama-server` command available
- Internet access for GitHub, Jira, and the initial model download
- Optional: a Jira Cloud account and API token for Jira analysis

The local model requires several GB of disk space and sufficient memory
to load a quantized 7B model. Generation speed depends on your hardware.

## Install the project

Clone the repository and enter its directory:

```bash
git clone <YOUR_REPOSITORY_URL> delivery-risk-agent
cd delivery-risk-agent
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install Python and frontend dependencies:

```bash
python -m pip install -e ".[dev]"
npm --prefix frontend ci
```

## Optional: configure private GitHub access

Public repositories can be analyzed without a GitHub token.

To analyze private repositories, create a fine-grained personal access
token in GitHub:

1. Open GitHub Settings → Developer settings → Personal access tokens
   → Fine-grained tokens.
2. Select the repository owner and repositories you want to analyze.
3. Grant these repository permissions:
   - Pull requests: Read
   - Checks: Read
4. Generate the token and add it to `.env` in the repository root:

    GITHUB_TOKEN=your_github_token

If `.env` already contains Jira configuration, add this line to the
existing file.

The token must have access to the private repository. Organization-owned
repositories may also require approval.

Restart the backend after changing configuration.

Without a token, requests use public unauthenticated access. With a token,
requests use authenticated access. An invalid or expired token can cause
requests to fail even for public repositories.

Keep the token in the backend configuration. Never commit `.env` or put
the token in frontend code.

## Optional: configure Jira Cloud

Skip this section if you only want GitHub analysis.

Create an API token without scopes using your Atlassian account:
https://id.atlassian.com/manage-profile/security/api-tokens

Create `.env` in the repository root:

```dotenv
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```

The configured account must be able to read the project's issues.

The dashboard accepts a project key, such as `RISK`. It uses the Jira site
and credentials configured in the backend. `JIRA_PROJECT_KEY` is used by
the Jira command-line reader.

Keep `.env` private. It is excluded from Git. Never put the token in
frontend code.

## Run the dashboard locally

Keep three terminals running.

### Terminal 1: local AI model

Install llama.cpp using its installation guide:
https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md

On macOS with Homebrew:

```bash
brew install llama.cpp
```

Start the model server:

```bash
llama-server \
  -hf lmstudio-community/Qwen2.5-7B-Instruct-GGUF:Q4_K_M \
  --alias qwen-local \
  --jinja \
  -ngl 0 \
  --port 8080
```

On Windows, enter the command on one line.

The first run downloads the model. Wait until the server is ready before
submitting an analysis.

The application connects to `http://localhost:8080/v1` and uses the model
alias `qwen-local`. No OpenAI API key is required.

This command uses CPU inference. Analysis has taken around five minutes
on the development machine; other machines may be faster or slower.

### Terminal 2: FastAPI backend

From the repository root, activate the virtual environment and run:

```bash
python -m uvicorn delivery_risk_agent.api:app --reload
```

Interactive API documentation:
http://localhost:8000/docs

### Terminal 3: React frontend

From the repository root:

```bash
npm --prefix frontend run dev
```

Open the URL printed by Vite, usually http://localhost:5173.

During development, Vite forwards `/api` requests to the backend on port
8000.

## Use the dashboard

### GitHub

1. Enter a repository URL, such as `https://github.com/owner/repo`.
   Public repositories work without a token. Private repositories require
   the backend token to have access.
2. Click **Analyze GitHub**.
3. Wait for the assessment to appear in the GitHub panel.

The application reads the first five open PRs and their GitHub check runs.

### Jira

1. Complete the Jira configuration above.
2. Enter a project key, such as `RISK`.
3. Click **Analyze Jira**.
4. Wait for the assessment to appear in the Jira panel.

The application follows pagination to read accessible project issues.

Each assessment shows a summary, risks, evidence, potential impact,
and recommended actions. Jira also shows the number of issues inspected.

## Try the rules without an AI model

From the repository root, with the virtual environment activated:

```bash
python -m delivery_risk_agent.report data/sample_project.json
```

The sample produces three findings: one critical and two high.

To fetch Jira issues and run only the rules:

```bash
python -m delivery_risk_agent.jira_reader
```

This uses `JIRA_PROJECT_KEY` from `.env`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/dashboard` | Rule-only analysis of the bundled sample |
| POST | `/api/analyze/github` | GitHub analysis with AI advice |
| POST | `/api/analyze/jira` | Jira analysis with AI advice |

GitHub request:

```json
{"repository_url": "https://github.com/owner/repo"}
```

Jira request:

```json
{"project_key": "RISK"}
```

## Run checks

From the repository root:

```bash
python -m pytest -v -m "not integration"
ruff check .
npm --prefix frontend run build
npm --prefix frontend run lint
```

Mocked API and Jira converter tests do not need external services.

To run the live AI integration tests, start the model server first.

macOS/Linux:

```bash
RUN_AGENT_TESTS=1 python -m pytest -v -m integration
```

Windows PowerShell:

```powershell
$env:RUN_AGENT_TESTS = "1"
python -m pytest -v -m integration
Remove-Item Env:RUN_AGENT_TESTS
```

## Troubleshooting

| Problem | What to check |
|---|---|
| npm cannot find `package.json` | Run from `frontend/`, or use `npm --prefix frontend ...` from the root |
| Local AI advisor unavailable | Confirm llama-server is ready on port 8080 with alias `qwen-local` |
| Analysis times out | The API allows up to 10 minutes for AI advice; check model-server logs |
| Jira authentication fails | Check your email, token, expiration, and token type |
| Jira returns no accessible issues | Check the project key, account permissions, and whether the project has issues |
| Unsupported Jira priority | Update `PRIORITY_MAPPING` in `jira_reader.py` for your project's names |
| | GitHub authentication fails | Check whether `GITHUB_TOKEN` is valid and unexpired |
| GitHub repository inaccessible | Check the URL, token repository access, read permissions, and organization approval |
| GitHub request denied | Check permissions and API rate limits |

## Current limitations

- GitHub analysis covers only the first five open PRs.
- GitHub checks that are pending or unknown are not treated as failing.
- GitHub reviews and linked work items are not fetched.
- Jira priority mappings currently support Highest, High, Medium, Low,
  and Lowest.
- Jira statuses are mapped using status categories. Blocked statuses and
  blocking links are not mapped yet.
- AI generation may take several minutes. Concurrent analyses share the
  same local model server and may take longer.
- No detected findings means the current rules found nothing in the
  inspected data; it does not establish that a project has no delivery risks.
- AI explanations and actions are suggestions for human review.
- This setup is intended for local use. The API has no application-level
  authentication.