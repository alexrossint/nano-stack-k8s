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

We want our database setup secured from the start, no plain-text passwords, storage that survives a crash, and a stable way for the app to find it.

- [Stage 4 - Deploy Postgres Pods with Volume, Secret and Service for both Namespaces](docs/stage-4-postges-pvc-secret-pod-service.md)

With the database ready, the app itself needs to run the same way, built from the same image, pointed at the right database, and reachable by something other than its own changing IP.

- [Stage 5 - Deploy App Pod and Service for "dev" and "prod" Namespaces](docs/stage-5-app-pods-dev-prod.md)

The real data still lived in the old Docker setup. Before trusting Kubernetes with production, we needed to move that data over safely, without losing anything, and without real downtime for users.

- [Stage 6 - Database migration and cutover](docs/stage-6-migration-cutover.md)

Clients were given raw port numbers to reach the app, not something we could hand out in a real company. We needed one clean, stable entry point instead.

- [Stage 7 - Expose the App with Ingress for "dev" and "prod"](docs/stage-7-ingress.md)

Right now, each app runs as exactly one Pod. If that one Pod crashes, or gets overwhelmed by traffic, there's no backup, no second copy to take the load or keep serving while it recovers.

- [Stage 8 - Scaling](docs/stage-8-scaling.md)

## What's Next

- ConfigMap, moving plain settings out of the Pod spec into their own object
- Health checks, liveness and readiness probes, the real fix for the `503` gap seen during scaling
- New app version 2.0, redesigned UI
- Rolling updates and rollbacks
- Resource limits
- Helm, packaging the whole setup as a reusable chart
- Basic CI/CD

## Concepts to Know, Not Built Here

A few real-world Kubernetes topics worth recognizing by name, even without hands-on practice in this project.

- RBAC, controlling who can do what inside a cluster
- NetworkPolicies, firewall-style rules between Pods
- StatefulSets, the proper way to run databases in Kubernetes, used a bare Pod here for simplicity
- Multi-node scheduling, this project runs on a single node, so pod placement across machines never comes into play