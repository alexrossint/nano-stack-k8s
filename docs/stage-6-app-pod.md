# Deploying the App to Kubernetes

Same idea as the Postgres Pod, just the app side this time, pointed at the new database instead of the old Docker one.

Checked the image is visible to the cluster first

```bash
colima ssh -- sudo k3s crictl images
```

Confirmed `nano-stack-app:1.0` was already visible to k3s, same image ID as the Docker build. Colima shares one Docker daemon under the hood, so no import step was needed.

 ## Create the file
`k8s/app/pod.yaml`

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

`DB_HOST: postgres` is the Service name, resolved by cluster DNS, same job the container name did on `nano-net`.

`DB_PASSWORD` pulls straight from the existing Secret `postgres-secret` using `valueFrom.secretKeyRef`, instead of a plain value. Same Secret Postgres uses, just consumed as an env var here instead of a mounted file.

No volumes, the app has nothing to persist itself.

## Apply and check

```bash
kubectl apply -f k8s/app/pod.yaml -n prod
```

```bash
kubectl get pod -n prod
```

Tested from inside the cluster, since the image has no `curl`

```bash
kubectl exec -n prod nano-app -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"
```

Got back the visitor counter HTML, confirming app to Service to new Postgres works end to end.