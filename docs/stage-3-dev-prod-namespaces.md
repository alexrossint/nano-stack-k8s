# Stage 3, Create the dev and prod namespaces

Before building anything real in Kubernetes, we set up two isolated spaces, `prod` for the real app and its data, `dev` as a safe sandbox to test changes in first, with no risk to the live app.

## Step 1, create the namespaces

A namespace is a separate area inside one cluster, its own set of objects, isolated from everything else.

### Create prod

```bash
kubectl create namespace prod
```

### Create dev

```bash
kubectl create namespace dev
```

### Check it

```bash
kubectl get namespaces
```

Shows both `prod` and `dev` listed alongside `default` and the built-in system namespaces.

## Step 2, folder structure

Each environment gets its own fully separate folder, no shared files between them.

```
k8s/dev/app/
k8s/dev/postgres/
k8s/prod/app/
k8s/prod/postgres/
```

Each environment is fully self-contained, explicit duplication over shared templating, easier to reason about, especially while still learning. A whole environment can still be applied in one command

```bash
kubectl apply -R -f dev -n dev
```

## What comes next

With both namespaces ready, the plan going forward is to build the Postgres and app pieces once in `dev`, prove they work end to end with a clean, empty database, then build the same setup in `prod`, and finish with the database migration and cutover happening together as one step.