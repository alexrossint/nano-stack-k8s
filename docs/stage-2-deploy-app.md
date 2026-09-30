# Stage 2, Write app, build and run the web service

With the environment prepped, network `nano-net`, volume `nano-pgdata`, Postgres running, the database is waiting, and now we need an app to talk to it.

## Step 1, write the app

The developer's part is a Flask file, `app.py`. It connects to Postgres, adds 1 to a counter and shows the number. It doesn't know where the DB is, so it asks for 4 values from outside, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. That's the handover between dev and devops.

The app needs Flask and psycopg2 to work, so we list them in `requirements.txt`. pip reads that list at build time and installs them, plus their dependencies. Later, `import` in the code picks them up from the image.

## Step 2, pack it into an image

A container starts as an empty box, so the Dockerfile is the recipe that packs it, Python, the packages, then our code.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

`RUN` happens once, at build time, and fills the image with packages. `CMD` happens every time a container starts. The list is copied before the code, so a code change doesn't redo the slow install.

### Build it

```bash
docker build -t nano-stack-app ./app
```

### Tag it

`latest` is just a moving label, so give it a real version.

```bash
docker tag nano-stack-app:latest nano-stack-app:1.0
```

## Step 3, start the app

The image is ready, so now we start a container from it, on the same network as Postgres, with the 4 values.

```bash
docker run -d \
  --name nano-app \
  --network nano-net \
  -e DB_HOST=postgres \
  -e DB_NAME=nanostack \
  -e DB_USER=nanouser \
  -e DB_PASSWORD=nanopass123 \
  -p 5001:5000 \
  nano-stack-app:1.0
```

The network is what lets the app find Postgres by name. We publish a port only for the app, because the browser needs to reach it. The database stays internal.