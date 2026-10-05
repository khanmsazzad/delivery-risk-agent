# Delivery Risk Dashboard Frontend

A React + TypeScript frontend built with Vite. It displays project details,
risk severity, evidence, and recommendations from the FastAPI backend.

See the [project README](../README.md#run-the-dashboard-locally) for instructions
on running the backend and frontend together.

## Local development

From this directory:

npm ci
npm run dev

Open the URL printed by Vite, usually http://localhost:5173.
The FastAPI backend must also be running on port 8000.

During development, Vite forwards `/api` requests to the backend.

## Checks

npm run build
npm run lint

The build command checks TypeScript and creates production files in `dist/`.

## Current scope

The dashboard displays findings from `data/sample_project.json`.
Live GitHub data and AI advice are not connected to the frontend yet.