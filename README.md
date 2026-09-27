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

## Learning Path
- Stage 0.1 - Create GitHub repo
- Stage 0 — Run app + DB with plain Docker
- Stage 1 — First Kubernetes Pod
- Stage 2 — Deployments
- Stage 3 — Services
- Stage 4 — ConfigMaps & Secrets
- Stage 5 — Persistent storage
- Stage 6 — Multi-service app (web + DB)
- Stage 7 — Namespaces
- Stage 8 — Ingress
- Stage 9 — Scaling
- Stage 10 — Health checks
- Stage 11 — Rolling updates & rollbacks
- Stage 12 — Resource limits
- Stage 13 — Helm packaging
- Stage 14 — Basic CI/CD