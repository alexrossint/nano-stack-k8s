# Nano Stack

A small learning project simulating a 2-person startup building
and deploying a simple web app, step by step, from plain Docker
to a Kubernetes setup — all running locally.

## Goal
Learn Kubernetes fundamentals through a hands-on, staged project
rather than isolated examples. Each stage adds one new concept.

## The App
A minimal Flask web app + Postgres database.
The app shows a page and counts visitors, storing the count in the database.
The app itself is intentionally simple — the focus is the infrastructure around it.

## Tech Stack
- Python (Flask)
- PostgreSQL
- Docker
- Kubernetes (via Colima)
- kubectl

## Stages
- Stage 0 - Create GitHub repo
- [Stage 1 - Prepare the env](docs/stage-1-env.md)
- [Stage 2 - Write app, build and run](docs/stage-2-3-app.md)
- Stage 3 — Run app and build its image
- Stage  — First Kubernetes Pod
- Stage  — Deployments
- Stage  — Services
- Stage  — ConfigMaps & Secrets
- Stage — Persistent storage
- Stage  — Multi-service app (web + DB)
- Stage  — Namespaces
- Stage  — Ingress
- Stage  — Scaling
- Stage — Health checks
- Stage — Rolling updates & rollbacks
- Stage — Resource limits
- Stage — Helm packaging
- Stage — Basic CI/CD