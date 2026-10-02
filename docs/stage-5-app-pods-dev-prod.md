# Stage 5, Deploy the app Pods and Service for dev and prod

With Postgres running in both namespaces, we deploy the app itself the same way, once in `dev` to prove it connects correctly to a clean database, once in `prod` pointed at the same setup, each namespace with its own self-contained folder. Then we expose the app with a Service, so it can be reached from outside the cluster too.

## Step 1, confirm the image is visible to the cluster

The app image was built locally with `docker build`, not pulled from a registry. Colima shares one Docker daemon under the hood, so the cluster's own runtime can already see it, worth confirming before relying on it.

### Check it

```bash
colima ssh -- sudo k3s crictl images
```

`nano-stack-app:1.0` shows up in the list, same image ID as the Docker build, confirming no import step is needed.

## Step 2, create the app Deployment

Same job `docker run nano-stack-app:1.0` did before, this time reading its database connection details from Kubernetes objects instead of `-e` flags typed by hand.

Created the file, `k8s/dev/app/deployment.yaml`, and the same file, `k8s/prod/app/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nano-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nano-app
  template:
    metadata:
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
`replicas` and `selector` wrap the container definition in a template, so Kubernetes can create and manage multiple identical copies rather than one fixed Pod.
`labels: app: nano-app` tags the Pods, so a Service can find them.

### Apply it, dev

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
```

### Apply it, prod

```bash
kubectl apply -f prod/app/deployment.yaml -n prod
```

### Check it

```bash
kubectl get pods -n dev
kubectl get pods -n prod
```

Both show `Running`, Pod names are auto-generated, proof they're managed by the Deployment.

## Step 3, test the app from inside the cluster

Before exposing anything outside the cluster, confirm the app can actually reach its database internally, proving the whole chain (app, Service, Postgres) works.

The base image has no `curl` installed, so the test uses Python's own built-in web client instead, already inside the image.

### Test dev

```bash
kubectl exec -n dev deploy/nano-app -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"
```

Returns the app's HTML, showing "visitor number 1", dev's own fresh, empty database, confirming the app connects correctly to it.

### Test prod

```bash
kubectl exec -n prod deploy/nano-app -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"
```

Returns the same HTML, this time against prod's database, confirming the same chain works there too, each namespace fully isolated from the other.

## Step 4, expose the app with a Service

The tests above only proved the app works from inside the cluster. To reach it from a browser on the Mac, the app needs a Service of type `NodePort`, which opens a port on the node itself, unlike Postgres's `ClusterIP`, which stays internal only.

Created the file, `k8s/dev/app/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nano-app
spec:
  type: NodePort
  selector:
    app: nano-app
  ports:
    - port: 5000
      targetPort: 5000
      nodePort: 30080
```

Created the same file for prod, `k8s/prod/app/service.yaml`, with one value changed

```yaml
      nodePort: 30081
```

`type: NodePort` makes this Service reachable from outside the cluster, not just from other Pods.
`selector: app: nano-app` matches the label on the app Pods.
`nodePort` is the actual external port, must fall within Kubernetes' reserved range, 30000 to 32767. NodePort numbers are cluster-wide, not scoped per namespace, so dev and prod can't share the same one, dev uses `30080`, prod uses `30081`.

### Apply it, dev

```bash
kubectl apply -f dev/app/service.yaml -n dev
```

### Apply it, prod

```bash
kubectl apply -f prod/app/service.yaml -n prod
```

### Check it

```bash
kubectl get svc -n dev
kubectl get svc -n prod
```

Shows `nano-app`, type `NodePort`, with ports `5000:30080/TCP` in dev and `5000:30081/TCP` in prod.

### Test it

```bash
curl http://localhost:30080
curl http://localhost:30081
```

Dev returns "visitor number 1", its own fresh database. Prod returns its own counter, confirming the app is now reachable from outside the cluster in both namespaces.

## Note, folder structure

Each environment's app objects live fully separately, no shared file between `dev` and `prod`.

```
k8s/dev/app/deployment.yaml
k8s/dev/app/service.yaml
k8s/prod/app/deployment.yaml
k8s/prod/app/service.yaml
```

A whole environment's app objects can also be applied in one go

```bash
kubectl apply -R -f dev/app -n dev
```