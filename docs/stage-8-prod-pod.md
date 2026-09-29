# Exposing the App in Prod, Manual Port Change

Dev already had `k8s/app/service.yaml` applied with `nodePort: 30080`. 
To expose the same app in prod, the same file was reused, only the `nodePort` 
value was changed before applying, since NodePort numbers are cluster-wide and can't repeat across namespaces if both are exposed at once, unlike internal Service ports.

### Edited the file

Changed `nodePort: 30080` to `nodePort: 30081` directly in `k8s/app/service.yaml`.

### Applied into prod

```bash
kubectl apply -f k8s/app/service.yaml -n prod
```

### Confirmed dev was unaffected

```bash
kubectl get svc -n dev
kubectl get svc -n prod
```

Dev still showed `30080`,prod now showed `30081`, since dev wasn't reapplied, only prod picked up the file's new value.

### Tested prod

```bash
curl http://localhost:30081
```

Returned the real migrated counter, confirming prod's app, Service, and Postgres all work correctly end to end.

### Known downside

Manually editing the same file back and forth between environments isn't scalable, and it's easy to forget which environment currently has which value. Kustomize and Helm both solve this properly with environment-specific overlays or values files, planned as a later stage instead of fixing it here.