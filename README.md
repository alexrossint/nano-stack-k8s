# Nano Stack

A small learning project simulating a 2-person startup building
and deploying a simple web app, step by step, from plain Docker
to a migration to Kubernetes setup — all running locally.

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
- helmw

## Stages (are updated as the project goes)
We create an enviroment in Docker because it seemed easy at the moment. Simple, fast shipping and not really secured.
- [Stage 1 - Prepare the enviroment in Docker](docs/stage-1-enviroment-docker.md)
- [Stage 2 - Write app, build and run the web service](docs/stage-2-deploy-app.md)

Our user database is growing, latency spikes and crashes during weekends. We cannot maintain it in Docker anymore. 
A decision was made to migrate to kubernetes and make it more secure and scalable to traffic spikes.
- [Stage 3 - Create postgres pod with secret and PVC volume](stage-3-postges-pvc-pod.md)
- [Stage 4 - Create a service for the postgres pod](stage-4-service.md)
- [Stage 5 — Database migration from Container to Pod](stage-5-db-migration.md)
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
