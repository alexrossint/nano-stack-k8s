# Stage 8, Scaling

Each app ran as exactly one Pod. If it crashed, nothing replaced it, no self-healing. If traffic spiked, one Pod had to absorb all of it alone, nothing shared the load. This stage converts the app from a bare Pod into a Deployment, an object that manages a desired number of identical Pods and keeps that number true over time.

## Step 1, convert the Pod into a Deployment

A bare Pod is just one instance, there's no way to tell it "run 3 of yourself", and nothing restarts it if it dies. A Deployment describes a template for a Pod, plus a number, how many copies should always be running.

Created the file, `k8s/app/deployment.yaml`

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

The container section is identical to the old Pod file, just nested inside `template`. `apiVersion` changes to `apps/v1`, `kind` changes to `Deployment`. `replicas` sets how many copies should exist. `selector` tells the Deployment which Pods, by label, belong to it, matching the label set inside the template.

## Step 2, dev, delete first then scale

In dev, the old bare Pod was deleted first.

```bash
kubectl delete pod nano-app -n dev
```

Then the Deployment was applied with `replicas: 1`.

```bash
kubectl apply -f k8s/app/deployment.yaml -n dev
```

### Check it

```bash
kubectl get pods -n dev
```

The Pod now has an auto-generated name, like `nano-app-57bbb7b556-wc5kt`, instead of the fixed name used before, proof it's managed by the Deployment, not a standalone Pod.

## Step 3, confirm self-healing

Deleted the running Pod directly, on purpose, to see what happens.

```bash
kubectl delete pod nano-app-57bbb7b556-wc5kt -n dev
```

With a bare Pod, this would leave nothing running. With a Deployment, a replacement Pod gets created automatically, reconciling back to the desired state.

### Check it

```bash
kubectl get pods -n dev
```

A new Pod appeared, different auto-generated name, same app, no manual action needed.

Watching the page auto-refresh during this moment showed a real, if brief, availability gap, a `503 Service Unavailable` from the ingress controller itself, since no Pod existed to route to for that short window.

## Step 4, scale up in dev

Changed `replicas: 1` to `replicas: 2` in `k8s/app/deployment.yaml`.

### Apply it

```bash
kubectl apply -f k8s/app/deployment.yaml -n dev
```

### Check it

```bash
kubectl get pods -n dev
```

Two `nano-app` Pods now running, each with its own auto-generated name, both behind the same Service.

## Step 5, confirm traffic is actually shared

Sent several requests in a row.

```bash
for i in {1..10}; do curl -s http://dev.nano.local > /dev/null; done
```

Checked each Pod's own logs afterward.

```bash
kubectl logs POD-NAME -n dev
```

Requests showed up in both Pods' logs, confirming the Service really does split traffic across all matching Pods, not just routing everything to one.

## Step 6, prod, scale first then delete

In prod, the order was reversed on purpose. The Deployment was applied first, already set to `replicas: 3`, while the old bare Pod was still running.

```bash
kubectl apply -f k8s/app/deployment.yaml -n prod
```

Only once the 3 new replicas were confirmed `Running` was the old Pod removed.

```bash
kubectl delete pod nano-app -n prod
```

Since the old Pod kept serving traffic the whole time the new replicas were starting up, the Service always had something to route to, no availability gap this time.

## Note, order matters

Two different orders were tried.

In dev, the old bare Pod was deleted first, then the Deployment was applied, afterward scaled up. This left a brief window where the Service had zero Pods to route to, resulting in a visible `503` from the ingress controller.

In prod, the Deployment was applied first with `replicas: 3`, bringing up new Pods while the old bare Pod was still running and serving traffic. Only after the new replicas were up was the old Pod deleted. This avoided any gap, the Service always had something to route to throughout the whole switch.

Scaling up before removing the old instance is the safer, closer to zero-downtime approach, worth remembering for real rollouts later.

## Concepts learned

A Deployment is not a running process itself, it's a standing rule the control plane continuously enforces, matching the Controllers piece covered in the Cluster note.
Auto-generated Pod names are a sign a Deployment (not a bare Pod) is managing them.
Self-healing has a real, visible recovery window when Pods are removed before replacements exist.
A Service load-balances automatically across every Pod matching its selector, scaling up Pods means the Service immediately starts spreading load across all of them, no extra configuration needed.
Bringing up new replicas before removing old instances avoids downtime entirely, this is the core idea behind zero-downtime deployments, covered more fully in the Rolling Updates stage later.