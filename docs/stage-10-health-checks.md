# Stage 10, Health checks, liveness and readiness probes

Back in Stage 8, deleting a Pod directly caused a brief `503`, the Service had zero healthy Pods to route to for a moment, and Kubernetes had no way to know a Pod wasn't actually ready to serve traffic yet. Health checks fix this by having Kubernetes actively ask each Pod "are you okay?", instead of assuming it's fine just because it's technically running.

## The two probes

Liveness probe, asks "are you still alive, or should I restart you?" If it fails enough times in a row, Kubernetes kills and restarts the container, catches a Pod that's running but frozen or stuck.

Readiness probe, asks "are you ready to receive traffic right now?" If it fails, the Pod stays running, Kubernetes just stops routing traffic to it through the Service, until it passes again.

## Step 1, add both probes to the Deployment

Updated `k8s/dev/app/deployment.yaml`, inside the container spec, alongside `ports`

```yaml
          ports:
            - containerPort: 5000
          readinessProbe:
            httpGet:
              path: /
              port: 5000
            initialDelaySeconds: 3
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
```

`httpGet: path, port` tells Kubernetes to send an HTTP request to that path and port, same as a manual `curl` test.
`initialDelaySeconds` waits this long after container start before the first check, avoids false failures while the app is still booting.
`periodSeconds` is how often to repeat the check, for the Pod's whole lifetime.

Readiness checks start sooner and run more often, since routing accuracy matters quickly. Liveness waits longer and checks less often, since restarting a container is more disruptive, worth being more cautious about.

### Apply it

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
```

### Check it

```bash
kubectl describe pod -n dev -l app=nano-app
```

Confirmed both probes attached correctly

```
Liveness:   http-get http://:5000/ delay=10s timeout=1s period=10s successThreshold=1 failureThreshold=3
Readiness:  http-get http://:5000/ delay=3s timeout=1s period=5s successThreshold=1 failureThreshold=3
```

## Step 2, test readiness, delete one Pod at a time

With 2 replicas running, deleted just one Pod.

```bash
kubectl delete pod POD-NAME -n dev
```

Watched the transition live

```bash
kubectl get pods -n dev -w
```

The new replacement Pod appeared as `0/1 Running` first, only flipping to `1/1` several seconds later, once its readiness check passed. During that whole window, the app stayed fully reachable, the other existing Pod kept serving traffic the entire time, no `503`, unlike deleting the only Pod back in Stage 8.

Deleting both Pods at once, by contrast, still caused a `503`, confirming readiness only protects traffic routing when at least one healthy Pod already exists, it can't serve traffic from zero Pods.

## Step 3, test liveness, force a failure on purpose

To actually see liveness trigger a restart, temporarily pointed it at a path that doesn't exist.

```yaml
          livenessProbe:
            httpGet:
              path: /this-does-not-exist
              port: 5000
```

Applied it, confirmed the change was picked up (`deployment.apps/nano-app configured`, not `unchanged`), then watched.

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
kubectl get pods -n dev -w
```

After the probe's delay and a few failed checks, `RESTARTS` increased on the running Pods, confirming the container was being killed and restarted in place by liveness, not replaced.

```
nano-app-74f6df75bc-g9jt9   1/1   Running   1 (7s ago)   67s
```

## Gotcha, both probes pointed at the same broken path

Since readiness also used `/`, pointing both probes at the same broken path caused readiness to fail too, which compounded the problem, Pods kept getting marked unready and killed in a cascading loop, several Pods ended in `Error` and had to be fully replaced rather than cleanly restarted.

Real setups usually use separate paths for liveness and readiness (for example `/healthz` vs `/ready`), so one broken dependency doesn't cause both checks to fail at once.

## Step 4, revert

Changed the liveness path back to `/`, applied again, confirmed the app settled back to a clean state.

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
kubectl get pods -n dev
```

Back to `1/1 Running`, `0` restarts, confirmed with

```bash
curl http://dev.nano.local
```

## Concepts learned

Readiness controls traffic routing, it can pull a Pod out of rotation without killing it, and bring it back once healthy again.
Liveness controls the container's own lifecycle, it restarts a stuck container, separate from whether it's currently receiving traffic.
Readiness only prevents downtime if at least one other healthy Pod already exists, it can't help if every Pod is unhealthy or deleted at once.
Pointing both probes at the same endpoint risks one broken dependency causing both failures at once, worth using distinct checks in a real setup.
Applying a change only changes the Deployment's Pod template, Kubernetes always creates new Pods to match it, a "restart" from liveness happens inside an existing Pod, a template change always rolls out new ones.

## Note, prod

Prod's `deployment.yaml` has the same readiness and liveness probes added, the hands-on failure tests (readiness delete, liveness break-and-restore) were only run in `dev`, not repeated against prod.