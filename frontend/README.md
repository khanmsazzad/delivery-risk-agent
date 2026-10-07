# Delivery Risk Dashboard Frontend

A React + TypeScript interface built with Vite.

The dashboard provides separate GitHub and Jira analysis panels. Each
panel displays its own progress, errors, and AI assessment.

GitHub analysis supports public repositories and private repositories
accessible through the backend's optional `GITHUB_TOKEN`. Jira analysis
uses the site and credentials configured in the backend. See the project
README for authentication setup.

See the [project README](../README.md) for complete installation,
Jira configuration, and model-server instructions.

## Development

From this directory:

```bash
npm ci
npm run dev
```

Keep FastAPI running on port 8000 and the local model server on port 8080.
Vite forwards `/api` requests to FastAPI during development.

## Checks

```bash
npm run build
npm run lint
```

The build checks TypeScript and generates frontend files in `dist/`.
The API proxy is a development setting; production hosting requires
separate API routing configuration.