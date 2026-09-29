# Create dev Namespace and Test the App

Data is growing and prod cannot be a testing ground. This stage creates an isolated `dev` namespace, a full copy of the prod setup, database included, so future app changes can be tested safely before touching real data.

### Create the namespace

```bash
kubectl create namespace dev
```

### Recreate the database pieces in dev

Same YAML files as prod, none of them hardcode a namespace, so they're reused as is, just pointed at `dev` instead.

```bash
kubectl create secret generic postgres-secret --from-literal=password="$(openssl rand -hex 16)" -n dev
```

Separate namespace means a fully separate Secret, dev gets its own random password, not shared with prod.

```bash
kubectl apply -f k8s/postgres/pvc.yaml -n dev
```

```bash
kubectl apply -f k8s/postgres/pod.yaml -n dev
```

```bash
kubectl apply -f k8s/postgres/service.yaml -n dev
```

Same reasoning as prod, dev needs its own database, so a broken test never risks the real data.

### Deploy the app into dev

```bash
kubectl apply -f k8s/app/pod.yaml -n dev
```

Same app image, same pattern, pointed at dev's own Postgres Service through `DB_HOST=postgres`, DNS names are scoped per namespace, so both dev and prod can use the exact same Service name without collision.

### Expose the app for testing

New file, `k8s/app/service.yaml`

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

`type: NodePort` opens the app outside the cluster, unlike the database's `ClusterIP`, which stays internal only.
`nodePort: 30080` is the external port, must fall in Kubernetes' reserved range, 30000 to 32767.

Internal ports (5432, 5000) don't need to differ between dev and prod, since Services live inside their own namespace. NodePort is the one exception, it's cluster-wide, so dev and prod would need different NodePort numbers if both were exposed at the same time.

```bash
kubectl apply -f k8s/app/service.yaml -n dev
```

### Test it

```bash
kubectl get svc -n dev
```

```bash
curl http://localhost:30080
```

Returned the app's page, "You are visitor number 1", dev's own fresh, empty database, full chain (app, Service, Postgres) confirmed working inside an isolated namespace.

### Notes

NodePort is a simple way to expose something locally, real client-facing access in production normally goes through a LoadBalancer or Ingress instead, which is a later stage.
Dev's database is intentionally empty, not a copy of prod's data. If realistic testing is ever needed, prod's data could be copied in with the same `pg_dump` approach used for the original migration.