# Stage 4, Postgres in Kubernetes: volume, secret, pod, service

Building the database piece by piece: storage first, then the password, then the Pod that uses both, then a stable address to reach it. Every piece gets created twice, once in `dev` to prove it works safely, once in `prod` for the real thing, using the exact same files each time.

## Step 1, create storage for the database

Postgres needs somewhere to keep its data that survives even if the Pod restarts. In Docker this was `docker volume create`. In Kubernetes, you don't create storage directly, you file a request for it, called a PersistentVolumeClaim (PVC), and the cluster provisions the actual storage automatically.

Created the file, `k8s/postgres/pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

`accessModes: ReadWriteOnce` means one node can mount this volume at a time, right for a single database Pod.
`resources: requests: storage: 1Gi` is how much capacity we're asking for.
No `storageClassName` specified, so it uses the cluster's default class, `local-path`, which carves storage out of the node's own disk.

### Apply it, dev first

```bash
kubectl apply -f k8s/postgres/pvc.yaml -n dev
```

### Apply it, then prod

```bash
kubectl apply -f k8s/postgres/pvc.yaml -n prod
```

### Check it

```bash
kubectl get pvc -n dev
kubectl get pvc -n prod
```

Status shows `Pending` in both, which is expected, this particular storage class waits until an actual Pod uses the claim before creating the real volume.

## Step 2, create the database password

The password needs to exist before Postgres starts, so this comes before the Pod. Instead of typing it into a command or a file, it's generated randomly and stored as a Secret, a Kubernetes object made for sensitive values. Each namespace gets its own separate Secret, dev and prod never share a password.

### Create it, dev

```bash
kubectl create secret generic postgres-secret --from-literal=password="$(openssl rand -hex 16)" -n dev
```

### Create it, prod

```bash
kubectl create secret generic postgres-secret --from-literal=password="$(openssl rand -hex 16)" -n prod
```

`openssl rand -hex 16` generates 16 random bytes as text, the actual password never appears anywhere in the command itself.
`--from-literal=password=...` stores it under the key `password`.

### Check it

```bash
kubectl get secret postgres-secret -n dev
kubectl get secret postgres-secret -n prod
```

Shows the Secret exists in both, `DATA 1` confirming one key stored, the value itself isn't printed.

## Step 3, create the database Pod

This is the actual container, same job `docker run postgres:16` did before, but now it also connects to the storage and the password we just created.

Created the file, `k8s/postgres/pod.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres
  labels:
    app: postgres
spec:
  containers:
    - name: postgres
      image: postgres:16
      env:
        - name: POSTGRES_USER
          value: nanouser
        - name: POSTGRES_DB
          value: nanostack
        - name: POSTGRES_PASSWORD_FILE
          value: /etc/secrets/password
      ports:
        - containerPort: 5432
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: secret-vol
          mountPath: /etc/secrets
          readOnly: true
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: postgres-pvc
    - name: secret-vol
      secret:
        secretName: postgres-secret
```

`env` sets the plain, non-secret settings, same idea as `-e` flags in Docker.
`POSTGRES_PASSWORD_FILE` tells Postgres to read its password from a file instead of an environment variable, more secure than a plain value.
`volumes` at the bottom declares what's attached to the Pod, our PVC and our Secret, each given a nickname (`data`, `secret-vol`).
`volumeMounts` inside the container says where each attached thing appears, `data` lands at Postgres's actual data folder, `secret-vol` lands at `/etc/secrets`, making the password readable at `/etc/secrets/password`, matching what `POSTGRES_PASSWORD_FILE` expects.
`labels: app: postgres` tags this Pod, so a Service can find it later.

### Apply it, dev first

```bash
kubectl apply -f k8s/postgres/pod.yaml -n dev
```

### Apply it, then prod

```bash
kubectl apply -f k8s/postgres/pod.yaml -n prod
```

### Check it

```bash
kubectl get pod -n dev
kubectl get pod -n prod
```

Status goes from `ContainerCreating` to `Running` in both. At this point, each namespace's PVC also flips from `Pending` to `Bound`, since its Pod started using it.

## Step 4, create a stable address for the database, Service

A Pod's IP changes every time it restarts, so nothing should rely on that IP directly. A Service gives a fixed address in front of the Pod instead, similar to an F5 VIP sitting in front of a backend server, clients always hit the same address, even if what's behind it changes.

Created the file, `k8s/postgres/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

`selector: app: postgres` tells the Service which Pods to send traffic to, matching the label we set on the Pod.
`port` is the address other Pods use to reach this Service.
`targetPort` is the actual port it forwards to on the Pod.
No `type` set, so it defaults to `ClusterIP`, internal only, nothing outside the cluster can reach the database directly, matching the choice we made in Docker of never publishing Postgres's port.

### Apply it, dev first

```bash
kubectl apply -f k8s/postgres/service.yaml -n dev
```

### Apply it, then prod

```bash
kubectl apply -f k8s/postgres/service.yaml -n prod
```

### Check it

```bash
kubectl get svc -n dev
kubectl get svc -n prod
```

Shows `postgres` in both namespaces, type `ClusterIP`, each with its own fixed internal IP and port `5432`. Since names are scoped per namespace, both can be called simply `postgres`, dev's app will resolve to dev's database, prod's app will resolve to prod's database, no collision.