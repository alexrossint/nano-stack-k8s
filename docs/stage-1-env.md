# **Goal**

Build the infrastructure first (network, storage, database), so the app has everything waiting for it. Same order as on-prem: infra team first, then the app.

## **Roles**

The developer defines what the app needs, in `app.py`: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

Devops builds the environment and hands those 4 values over.

## **Run order**

```
network → volume → Postgres → app
```

## **Network** 🌐

```bash
docker network create nano-net
```

Private network. Containers on it find each other by container name (Docker's built-in DNS). Container name = the DB host address.

## **Volume** 💾

```bash
docker volume create nano-pgdata
```

Storage that lives outside the container, managed by Docker. The data survives if the container is deleted.

## **Postgres** 🐘

```bash
docker run -d \
  --name postgres \
  --network nano-net \
  -e POSTGRES_USER=nanouser \
  -e POSTGRES_PASSWORD=nanopass123 \
  -e POSTGRES_DB=nanostack \
  -v nano-pgdata:/var/lib/postgresql/data \
  postgres:16
```

**Flags:**

- `d` → run in the background
- `-name postgres` → container name, also its DNS name on the network
- `-network nano-net` → attach to our network
- `e POSTGRES_USER / PASSWORD / DB` → Postgres creates this user, password and database on first start
- `v nano-pgdata:/var/lib/postgresql/data` → mount the volume at Postgres's data folder

`postgres:16` → image with a pinned version

No `-p` → the port is not published, so only containers on `nano-net` can reach the DB

## **Verify** ✅

```bash
docker logs postgres
```

Expected last line: `database system is ready to accept connections`

## **Values handed to the app**

```
DB_HOST=postgres
DB_NAME=nanostack
DB_USER=nanouser
DB_PASSWORD=nanopass123
```

## **Concepts learned**

`localhost` inside a container = the container itself, not another container

Environment variables = the app's config, set from outside the code

The app never picks the DB, whoever runs it sets `DB_HOST`

Packages in `requirements.txt` are installed into the image at build time

**What this becomes in Kubernetes**

```
docker network create   →  cluster networking + Services
docker volume create    →  PersistentVolume + PVC
docker run -e ...       →  ConfigMap + Secret
docker run              →  Pod, then Deployment
```

**Note**

The password is in plain text here, which is fine for a lab. Kubernetes Secrets replace this later.