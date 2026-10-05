# Stage 13, Horizontal Pod Autoscaling

Replicas were fixed so far, 2 or 3, always, no matter how busy or idle the app actually was. This stage lets Kubernetes scale the number of replicas up and down on its own, based on real CPU usage, the same way a resource ceiling needed to come from real numbers back in Stage 12, autoscaling needed that same baseline to work.

## Why a maximum matters

Before building anything, worth thinking through why autoscaling isn't left uncapped. A node only has so much real CPU and memory, scaling forever eventually just leaves Pods stuck `Pending`, unable to find room. Cost is real too, in a cloud environment, more replicas usually means more money. And critically, every app replica here talks to the same single Postgres Pod, scaling the app alone doesn't scale what it depends on, a concern that turned out to be exactly right, as this stage ended up proving the hard way.

Picked `maxReplicas: 10` for dev, a deliberately safe, conservative number for a small local cluster.

## Step 1, write the HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nano-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nano-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
```

Saved as `dev/app/hpa.yaml`. `minReplicas` and `maxReplicas` set the floor and ceiling, `averageUtilization: 50` means "if CPU usage averages above 50% of what each Pod requested, scale up".

### Apply it

```bash
kubectl apply -f dev/app/hpa.yaml -n dev
```

### Check it

```bash
kubectl get hpa -n dev
```

Showed `cpu: <unknown>/50%` at first, expected, the HPA needs a moment to pull its first real metric. A short wait later, it showed a real number, confirming it was reading live usage.

## Step 2, build a way to generate real load

Our app barely uses any CPU under normal use, a quick `curl` wasn't going to prove anything. Added a temporary test-only route to `app.py`.

```python
@app.route("/stress")
def stress():
    import time
    end = time.time() + 5
    while time.time() < end:
        pass
    return "stress done"
```

Built it as a clearly separate, throwaway image, never meant to become a real version.

```bash
docker build -t nano-stack-app:stress-test ./app
```

Deployed it into dev, confirmed the app still responded normally before actually generating any load.

## Step 3, generate load, watch it scale

One quick burst wasn't enough, each `/stress` call finished in exactly 5 seconds, average CPU kept dropping back down before the HPA could react further. Sent sustained, repeated waves instead.

```bash
for round in {1..5}; do
  for i in {1..50}; do curl -s http://dev.nano.local/stress > /dev/null & done
  sleep 2
done
```

Watched it live.

```bash
kubectl get hpa -n dev -w
```

```
cpu: 200%/50%   2   10   5
```

Real, strong signal, 4x over target, replicas climbing fast, eventually reaching 9. Genuinely felt like a self-inflicted denial-of-service for a moment, worth being honest about that, a live `/stress` endpoint like this is exactly the kind of thing that should never exist in a real production app.

## Step 4, the real incident, Postgres nearly went down

With 9 app replicas suddenly live, the app started returning `503`s, not from CPU this time, something else was wrong.

```bash
kubectl get pods -n dev
```

```
postgres    0/1    OOMKilled
```

This was the actual lesson of this stage. 9 app Pods all trying to connect to the same single Postgres Pod overwhelmed its small `64Mi` memory limit from Stage 12, and it crashed repeatedly. Every app replica then failed its own readiness check, since none of them could reach a working database, the concern raised right at the start of this stage, scaling the app doesn't scale what it depends on, happened for real, not just in theory.

## Step 5, recovering

Raised Postgres's limits to give it breathing room under real connection pressure.

```yaml
          resources:
            requests:
              cpu: "50m"
              memory: "128Mi"
            limits:
              cpu: "200m"
              memory: "256Mi"
```

Postgres is a bare Pod, same limitation hit back in Stage 12, had to delete and reapply rather than update in place.

```bash
kubectl delete pod postgres -n dev
kubectl apply -f dev/postgres/pod.yaml -n dev
```

Postgres came back healthy, but the app Pods were already stuck in their own crash loop and didn't recover on their own, cleared them manually.

```bash
kubectl delete pod nano-app-5d6c779dd9-qkrc7 nano-app-5d6c779dd9-xddk6 -n dev
```

Everything settled back to healthy.

## Step 6, cleanup

Removed the stress-test image from the running Deployment, reverted back to a known-good real version.

```yaml
          image: nano-stack-app:2.0
```

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
```

Deleted the unused test image locally.

```bash
docker rmi nano-stack-app:stress-test
```

Confirmed nothing in the cluster still depended on it before removing it.

```bash
kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}'
```

## Concepts learned

An HPA needs resource `requests` defined first, it scales based on usage as a percentage of what was requested, not raw numbers.
A short burst of load doesn't show sustained scaling, average CPU can drop back down before the HPA reacts further, sustained load is needed to see real scale-up behavior.
`maxReplicas` is a safety rail, not a target, it exists to prevent a different failure, exhausted node capacity, runaway cost, an overwhelmed dependency, not to guarantee unlimited capacity.
Scaling one layer doesn't automatically protect what it depends on, 9 app replicas hammering one small Postgres Pod moved the bottleneck instead of fixing it, and nearly took the database down.
Test-only debug endpoints, like `/stress`, are a real security risk if they ever reach a real production app, worth removing entirely once testing is done.
Scale-down happens gradually, with an intentional cooldown, to avoid flapping replicas up and down from brief, temporary spikes.