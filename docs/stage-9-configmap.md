# Stage 9, ConfigMap: moving plain settings out of the Deployment

`DB_NAME` and `DB_USER` were typed directly into the Deployment's `env` section, mixed in with how the Pod itself is defined. A ConfigMap separates plain, non-sensitive config from the Pod spec entirely, same category of object as a Secret, just for values that don't need to be hidden.

## Step 1, create the ConfigMap

Created the file, `k8s/dev/app/configmap.yaml`, and the same file, `k8s/prod/app/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nano-app-config
data:
  DB_NAME: nanostack
  DB_USER: nanouser
```

Unlike most objects, a ConfigMap has no `spec`, just `data`, plain key-value pairs. It isn't "doing" anything active, it's just storage other objects read from.

### Apply it, dev

```bash
kubectl apply -f dev/app/configmap.yaml -n dev
```

### Apply it, prod

Each namespace needs its own copy, same as Secrets and everything else, nothing carries over automatically between namespaces.

```bash
kubectl apply -f prod/app/configmap.yaml -n prod
```

### Check it

```bash
kubectl get configmap nano-app-config -n dev
kubectl get configmap nano-app-config -n prod
```

## Step 2, read from it in the Deployment

Updated `k8s/dev/app/deployment.yaml` and `k8s/prod/app/deployment.yaml`, replacing the hardcoded `DB_NAME` and `DB_USER` values with references to the ConfigMap.

```yaml
          env:
            - name: DB_HOST
              value: postgres
            - name: DB_NAME
              valueFrom:
                configMapKeyRef:
                  name: nano-app-config
                  key: DB_NAME
            - name: DB_USER
              valueFrom:
                configMapKeyRef:
                  name: nano-app-config
                  key: DB_USER
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
```

Same `valueFrom` pattern already used for the Secret, just `configMapKeyRef` instead of `secretKeyRef`. `DB_HOST` stays hardcoded, it's always `postgres`, the Service name, not something that changes per environment here.

### Apply it

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
kubectl apply -f prod/app/deployment.yaml -n prod
```

### Check it

```bash
curl http://dev.nano.local
curl http://prod.nano.local
```

Both kept working, no downtime in either namespace, each already running multiple replicas (Stage 8), so the Deployment could roll old Pods out and new ones in gradually, always keeping at least one Pod available.

## What actually happened under the hood

Changing the Deployment's `env` section changed its Pod template. Since a Deployment's job is "keep Pods matching this exact template running", the old Pods no longer matched, so new ones were created with the updated config and the old ones were removed. This is a small live example of a rolling update, covered properly in a later stage.

## Gotcha hit

Forgot to apply the ConfigMap in prod before updating the Deployment there.

```
Warning  Failed  kubelet  spec.containers{nano-app}: Error: configmap "nano-app-config" not found
```

Fixed by applying the ConfigMap into `prod` first, confirming namespaces really are fully isolated, nothing assumed shared.

## Concepts learned

A ConfigMap has `data`, not `spec`, since it stores values rather than describing something that runs.
ConfigMaps and Secrets follow the same `valueFrom` pattern in a Pod's `env`, only the key name differs (`configMapKeyRef` vs `secretKeyRef`).
A ConfigMap can also be mounted as files in a volume, the same two-part `volumes` / `volumeMounts` pattern used for the Postgres Secret, each key becomes a file, useful for full config files rather than single values.
ConfigMaps mounted as files update automatically when changed, ConfigMaps used as environment variables do not, those require the Pod to restart to pick up new values.
Each namespace needs its own copy of a ConfigMap, same as Secrets, nothing is shared automatically across namespaces.

## Note, folder structure

```
k8s/dev/app/configmap.yaml
k8s/prod/app/configmap.yaml
```