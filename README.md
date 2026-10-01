# Nano Stack

A small learning project simulating a 2-person startup building and deploying a simple web app, from plain Docker through a migration to Kubernetes, all running locally.

## The Story

The app started simple, one Flask container, one Postgres container, run by hand with `docker run`. It worked fine for a while, fast to ship, nothing complicated.

As usage grew, cracks showed: no self-healing when something crashed, no isolated environment to test changes safely, passwords typed into plain commands, no clean way to update or roll back. A decision was made to migrate to Kubernetes, securing the setup, adding a proper dev environment, and building toward something that could scale under real traffic.

## Goal

Learn Kubernetes fundamentals through a hands-on, staged project rather than isolated examples. Each stage builds on the last, and the two problems above (why Docker alone wasn't enough, why the database needed a real migration) shape the order the project follows.

## The App

A minimal Flask web app plus a Postgres database. It shows a page and counts visitors, storing the count in the database. The app itself is intentionally simple, the focus is the infrastructure around it.

## Prerequisites

Using Colima with Kubernetes on Mac, lightweight and easy to get running via Homebrew.

```bash
brew install colima
brew install kubectl
colima start --kubernetes
```

Docker Desktop with Minikube can also work as an alternative.

## Tech Stack

- Python (Flask)
- PostgreSQL
- Docker
- Kubernetes, via Colima
- kubectl

## Stages

*(updated as the project goes)*

We created an environment in Docker because it seemed easy at the moment, simple, fast to ship, not really secured.

- [Stage 1 - Prepare the enviroment in Docker](docs/stage-1-enviroment-docker.md)
- [Stage 2 - Write app, build and run the web service](docs/stage-2-deploy-app.md)

Our user database is growing, latency spikes and crashes during weekends. We cannot maintain it in Docker anymore.
A decision was made to migrate to Kubernetes and make it secured and scalable to traffic spikes. We also create a DEV
enviroment to test new features in the future.

- [Stage 3 - Create "dev" and "prod" Namespaces](docs/stage-3-dev-prod-namespaces.md)
- [Stage 4 - Deploy Postgres Pods with Volume, Secret and Service for both Namespaces](docs/stage-4-postges-pvc-secret-pod-service.md)
- [Stage 5 - Deploy App Pod and Service for "dev" and "prod" Namespaces](docs/stage-5-app-pods-dev-prod.md)
- [Stage 6 - Database migration and cutover](docs/stage-6-migration-cutover.md)
- [Stage 7 - Expose the App with Ingress for "dev" and "prod"](docs/stage-7-ingress.md)

## What's Next

- Ingress, a real hostname instead of a raw NodePort
- Scaling, running multiple replicas of the app
- Health checks, liveness and readiness probes
- Rolling updates and rollbacks
- Resource limits
- Helm, packaging the whole setup as a reusable chart
- Basic CI/CD