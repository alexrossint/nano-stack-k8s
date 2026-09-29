# Nano Stack

A small learning project simulating a 2-person startup building
and deploying a simple web app, step by step, from plain Docker
to a migration to Kubernetes setup — all running locally.

## Goal
Learn Kubernetes fundamentals through a hands-on, staged project
rather than isolated examples. Each stage adds on new concept.

## The App
A minimal Flask web app + Postgres database.
The app shows a page and counts visitors, storing the count in the database.
The app itself is intentionally simple — the focus is the infrastructure around it.

## Prerequisites
I am using Colima with Kubernetes on Mac because it's lightweight and easy to get running via Homebrew:
```bash
brew install colima
brew install kubectl
colima start --kubernetes
```
Docker Desktop app with Minikube can also work.

## Tech Stack
- Python (Flask)
- PostgreSQL
- Docker & Kubernetes kubectl (via Colima)
- helm

## Stages (are updated as the project goes)
We create an enviroment in Docker because it seemed easy at the moment. Simple, fast shipping and not really secured.
- [Stage 1 - Prepare the enviroment in Docker](docs/stage-1-enviroment-docker.md)
- [Stage 2 - Write app, build and run the web service](docs/stage-2-deploy-app.md)

Our user database is growing, latency spikes and crashes during weekends. We cannot maintain it in Docker anymore. 
A decision was made to migrate to Kubernetes and make it secured and scalable to traffic spikes. We also create a DEV
enviroment to test new features in the future.
- [Stage 3 - Create postgres pod with secret and PVC volume](docs/stage-3-postges-pvc-pod.md)
- [Stage 4 - Create a service for the postgres pod](docs/stage-4-service.md)
- [Stage 5 - Database migration from Container to Pod](docs/stage-5-db-migration.md)
- [Stage 6 - Building the app Pod](docs/stage-6-app-pod.md)
- [Stage 7 - Create dev (env) namespace and test the app before prod launch](docs/stage-7-dev-namespace.md)
- Stage  — Namespaces
- Stage  — Ingress
- Stage  — Scaling
- Stage — Health checks
- Stage — Rolling updates & rollbacks
- Stage — Resource limits
- Stage — Helm packaging
- Stage — Basic CI/CD
