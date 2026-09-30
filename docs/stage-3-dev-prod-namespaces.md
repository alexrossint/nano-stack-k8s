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

## Step 2, keep the YAML files namespace-agnostic

None of the files we write specify a namespace inside `metadata`, on purpose. This means the exact same file can be applied into either namespace just by changing the `-n` flag on `kubectl apply`, no duplicating files, no editing between environments.

### Confirm no file hardcodes a namespace

```bash
grep -r namespace k8s/
```

Empty output confirms it, whichever namespace is passed at apply time decides where the object lands.

## What comes next

With both namespaces ready, the plan going forward is to build the Postgres and app pieces once, apply them into `dev` first and prove they work end to end with a clean, empty database, then apply the same files into `prod`, and finish with the database migration and cutover happening together as one step.