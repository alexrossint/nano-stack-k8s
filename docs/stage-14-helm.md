# Stage 14, Helm: one chart for dev and prod

The `k8s/dev` and `k8s/prod` folders were about 99 percent identical. Changing a probe or a resource limit meant editing the same line in two places. Helm fixes this by keeping one set of template files with blanks in them, and a small values file per environment that fills the blanks in.

## Step 1, install Helm

```bash
brew install helm
```

### Check it

```bash
helm version
```

## Step 2, build the chart from the real files

`helm create` generates a generic starter chart, but it doesn't know about our env vars, probes or Postgres. Instead, the chart is built from the files that already work.

Created a folder `nano-stack/` in the repo root with this structure.

```
nano-stack/
  Chart.yaml
  values.yaml
  values-dev.yaml
  values-prod.yaml
  templates/
    app/
      configmap.yaml
      deployment.yaml
      hpa.yaml
      ingress.yaml
      service.yaml
    postgres/
      pod.yaml
      pvc.yaml
      service.yaml
```

`Chart.yaml` is the chart's identity card (name and version), and Helm needs it. Everything inside `templates/` becomes real Kubernetes objects. The values files are only input, so they stay outside. The dev files were copied in unchanged, and `values.yaml` started empty.

### Check it

```bash
helm template nano-stack nano-stack/ | grep "^kind:"
```

`helm template` prints the final YAML without touching the cluster. It showed 8 objects.

## Step 3, install into dev

Helm refuses to take over objects it didn't create. Objects made with `kubectl apply` have no Helm labels, so the install fails with an "invalid ownership metadata" error. The old dev objects had to be deleted first.

```bash
kubectl delete -R -f k8s/dev -n dev
```

This also deletes the PVC, so the database starts empty. The `postgres-secret` stays, because it was created by command and isn't in any file.

### Install it

```bash
helm install nano-stack nano-stack/ -n dev
```

`nano-stack` is the release name, Helm's name for one installed copy of the chart.

### Check it

```bash
helm list -n dev
```

## Step 4, replace repeated values with blanks

The method was the same for every file. Open it, find a value that repeats or differs, and replace it with a blank.

A blank is written `{{ .Values.name }}`. Helm looks up `name` in the values files and puts the value in its place. `.Values` must be spelled this way, because Helm provides it as a built-in. The part after it is whatever name you chose in your values file, and the case must match exactly.

The names and ports that repeat across files became shared values in `values.yaml`.

```yaml
appName: nano-app
appPort: 5000
domain: nano.local

dbHost: postgres
dbName: nanostack
dbUser: nanouser

pvcName: postgres-pvc
pgStorage: 1Gi

minReplicas: 2
maxReplicas: 10
cpuTarget: 50

cpuRequest: 10m
memoryRequest: 25Mi
cpuLimit: 20m
memoryLimit: 50Mi

PGcpuRequest: 50m
PGmemoryRequest: 100Mi
PGcpuLimit: 100m
PGmemoryLimit: 200Mi

image:
  repository: nano-stack-app
```

The database values are used by both the app and Postgres, so the two can't disagree, which was the typo problem from Stage 2.

The Deployment's `replicas` line was deleted. The HPA owns the replica count, and leaving the line would reset it to 2 on every upgrade.

### The Ingress host comes from the namespace

Helm knows which namespace it is installing into, through `.Release.Namespace`. The host is built from it, so no environment name has to be typed anywhere.

```yaml
host: {{ .Release.Namespace }}.{{ .Values.domain }}
```

With `-n dev` this becomes `dev.nano.local`, and with `-n prod` it becomes `prod.nano.local`.

## Step 5, the values that differ per environment

Only two values differ, so these are the only entries in the environment files. Neither has a default in `values.yaml`, so an environment can't accidentally inherit the other's value.

`values-dev.yaml`

```yaml
nodePort: 30080

image:
  tag: "2.1"
```

`values-prod.yaml`

```yaml
nodePort: 30081

image:
  tag: "2.1"
```

The NodePort differs because NodePorts are cluster-wide, so dev and prod can't share one. The image tag lives here so dev can run a newer version than prod while a release is being tested.

In the templates they read as:

```yaml
nodePort: {{ .Values.nodePort }}
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
```

## Step 6, show the environment name on the page

The page title is plain text inside `app.py`, so Helm can't change it. The app has to read its environment name from a variable. In `app.py`, inside `index()`:

```python
env_name = os.environ.get("ENV_NAME", "")
```

and the title became `Nano Stack {env_name}`. This is a code change, so it needs a new image version.

```bash
docker build -t nano-stack-app:2.1 ./app
```

In the Deployment, one new entry under `env:` gives the variable the namespace name.

```yaml
            - name: ENV_NAME
              value: {{ .Release.Namespace }}
```

The same image now runs in both environments, and only the variable differs.

## Step 7, upgrade

```bash
helm upgrade nano-stack nano-stack/ -n dev -f nano-stack/values-dev.yaml
```

`upgrade` re-renders the chart and applies only what changed. Helm reads `values.yaml` on its own, but any other values file has to be named with `-f`, and Helm does not remember it between upgrades. Pass the same file every time.

### Check it

```bash
helm list -n dev
```

`REVISION` goes up by one with each upgrade. Pods are replaced only when the Pod template inside the Deployment changes (image, env, probes, resources), not when a Service or Ingress changes.

## Step 8, install into prod

The old prod objects had to be deleted first, for the same ownership reason.

```bash
kubectl delete -R -f k8s/prod -n prod
```

This also deletes prod's PVC, so the database starts empty. Take a `pg_dump` first if the data matters. The delete missed the Deployment and the HPA, so those were removed by name.

```bash
kubectl delete deployment nano-app -n prod
kubectl delete hpa nano-app -n prod
```

### Install it

```bash
helm install nano-stack nano-stack/ -n prod -f nano-stack/values-prod.yaml
```

## Gotchas hit along the way

Renaming the ConfigMap broke the Deployment. The Deployment referenced the old ConfigMap name in two places, so both had to be updated to the new value, or new Pods would fail with "configmap not found".

A YAML indentation error. After editing the `resources` block, the `readinessProbe` ended up at the wrong depth, and the upgrade failed with "mapping values are not allowed in this context". `resources`, `readinessProbe` and `livenessProbe` must all start at the same column.

A request larger than its limit. A typo set the Postgres memory request to `500Mi` against a `200Mi` limit, and Kubernetes rejected the Pod. A request can never be higher than its limit.

Postgres is a bare Pod, so changing its resources in place is not allowed. The Pod was deleted and the upgrade run again, and the data stayed on the PVC.

A misspelled value key does not raise an error. Helm renders an empty value, so a name like `PGcpuLimit` has to match in both files.

## What stays outside Helm

The `dev` and `prod` namespaces, created in Stage 3. Helm can create one with the `--create-namespace` flag, but it never owns it, and `helm uninstall` leaves it in place.

`postgres-secret` in each namespace. Putting it in the chart would put the password in a file in Git.

The nginx ingress controller. The cluster needs exactly one, shared by dev and prod. Our chart is installed twice, so including it would clash.

The lines in `/etc/hosts`.

## Note, the old folders

`k8s/dev` and `k8s/prod` stay in the repo as history, and the earlier stage docs point to them. They are no longer the source of truth. Running `kubectl apply` on them now would put the cluster out of sync with the chart.

## Concepts learned

A chart is a folder of templates with blanks, plus values files that fill them in. Helm combines them into the same YAML that was written by hand before.

`values.yaml` is loaded automatically and holds what is shared. Files named with `-f` are loaded on top and win when the same key appears in both.

`.Values` is the data from the values files. `.Release.Namespace` is the namespace passed with `-n`.

Helm only manages objects it created, and tracks them as a release with numbered revisions.

Anything that has to match in two files, like a name, a port or a database user, belongs in one value.