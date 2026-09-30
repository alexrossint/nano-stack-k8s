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
- [Stage 3 - Create "dev" and "prod" Namespaces](docs/stage-3-dev-prod-namespaces.md)
- [Stage 4 - Create Postgres Pods with Volume, Secret and Service](docs/stage-4-postges-pvc-secret-pod-service.md)
- [Stage 5 - Deploy App Pod for both Namespaces](docs/stage-5-app-pods-dev-prod.md)
- [Stage 6 - Database migration and cutover](docs/stage-6-migration-cutover.md)
- Stage  — Ingress
- Stage  — Scaling
- Stage — Health checks
- Stage — Rolling updates & rollbacks
- Stage — Resource limits
- Stage — Helm packaging
- Stage — Basic CI/CD
