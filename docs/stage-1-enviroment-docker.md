# Stage 1, Prepare the environment in Docker

Build the infrastructure first, network, storage, database, so the app has everything waiting for it. Same order as on-prem, infra team first, then the app.

The developer defines what the app needs, in `app.py`, four values: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Devops builds the environment and hands those values over.

Run order:

```
network, then volume, then Postgres, then the app
```

## Step 1, create the network

A private network. Containers on it find each other by container name, Docker's built-in DNS. The container name becomes the DB host address.

### Create it

```bash
docker network create nano-net
```

## Step 2, create the volume

Storage that lives outside the container, managed by Docker. The data survives even if the container is deleted.

### Create it

```bash
docker volume create nano-pgdata
```

## Step 3, run Postgres

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

`-d` runs it in the background.
`--name postgres` sets the container name, also its DNS name on the network.
`--network nano-net` attaches it to our network.
`-e POSTGRES_USER / PASSWORD / DB` creates this user, password and database on first start.
`-v nano-pgdata:/var/lib/postgresql/data` mounts the volume at Postgres's data folder.
`postgres:16` pins the image version.
No `-p`, the port is not published, so only containers on `nano-net` can reach the DB.

### Check it

```bash
docker logs postgres
```

Expected last line, `database system is ready to accept connections`.

## Values handed to the app

```
DB_HOST=postgres
DB_NAME=nanostack
DB_USER=nanouser
DB_PASSWORD=nanopass123
```

## Concepts learned

`localhost` inside a container means the container itself, not another container.
Environment variables are the app's config, set from outside the code.
The app never picks the DB, whoever runs it sets `DB_HOST`.
Packages in `requirements.txt` get installed into the image at build time.

## What this becomes in Kubernetes

```
docker network create   becomes cluster networking and Services
docker volume create    becomes PersistentVolume and PVC
docker run -e ...       becomes ConfigMap and Secret
docker run               becomes a Pod, then a Deployment
```

## Note

The password is in plain text here, fine for a lab. Kubernetes Secrets replace this later.