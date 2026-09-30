# Stage 5, Deploy the app Pods in dev and prod

With Postgres running in both namespaces, we deploy the app itself the same way, once in `dev` to prove it connects correctly to a clean database, once in `prod` pointed at the same setup, both using the same files.

## Step 1, confirm the image is visible to the cluster

The app image was built locally with `docker build`, not pulled from a registry. Colima shares one Docker daemon under the hood, so the cluster's own runtime can already see it, worth confirming before relying on it.

### Check it

```bash
colima ssh -- sudo k3s crictl images
```

`nano-stack-app:1.0` shows up in the list, same image ID as the Docker build, confirming no import step is needed.

## Step 2, create the app Pod

Same job `docker run nano-stack-app:1.0` did before, this time reading its database connection details from Kubernetes objects instead of `-e` flags typed by hand.

Created the file, `k8s/app/pod.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nano-app
  labels:
    app: nano-app
spec:
  containers:
    - name: nano-app
      image: nano-stack-app:1.0
      env:
        - name: DB_HOST
          value: postgres
        - name: DB_NAME
          value: nanostack
        - name: DB_USER
          value: nanouser
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
      ports:
        - containerPort: 5000
```

`DB_HOST: postgres` is the Postgres Service name from Stage 4, resolved by the cluster's internal DNS, same job the container name did on `nano-net` in Docker.
`DB_PASSWORD` pulls straight from the existing `postgres-secret` using `valueFrom.secretKeyRef`, instead of a plain value, so the password is never written in the file itself.
No volumes here, the app itself has nothing to persist.
`labels: app: nano-app` tags this Pod, so a Service can find it later.

### Apply it, dev first

```bash
kubectl apply -f k8s/app/pod.yaml -n dev
```

### Apply it, then prod

```bash
kubectl apply -f k8s/app/pod.yaml -n prod
```

### Check it

```bash
kubectl get pod -n dev
kubectl get pod -n prod
```

Both show `Running`.

## Step 3, test the app from inside the cluster

Before exposing anything outside the cluster, confirm the app can actually reach its database internally, proving the whole chain (app, Service, Postgres) works.

The base image has no `curl` installed, so the test uses Python's own built-in web client instead, already inside the image.

### Test dev

```bash
kubectl exec -n dev nano-app -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"
```

Returns the app's HTML, showing "visitor number 1", dev's own fresh, empty database, confirming the app connects correctly to it.

### Test prod

```bash
kubectl exec -n prod nano-app -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"
```

Returns the same HTML, this time against prod's database, confirming the same chain works there too, each namespace fully isolated from the other.