# Stage 12, Resource limits

Up to now, every Pod could use as much CPU and memory as it wanted, no ceiling at all. One runaway process could, in theory, eat up everything on the node, starving every other Pod running beside it. This stage puts real boundaries in place, requests as a reservation, limits as a hard ceiling.

## Checking real usage first

Before picking any numbers, checked what the app and Postgres were actually using, idle, under normal conditions.

```bash
kubectl top pod -n dev --containers
```

```
nano-app    4-5m CPU    23-24Mi memory
postgres    8m CPU      35Mi memory
```

Genuinely tiny numbers, a lightweight Flask app and a lightly used Postgres. These real figures became the basis for every request and limit value chosen afterward, not guesswork.

## Adding resources to the app

Added alongside the existing `ports` and probes in the container spec.

```yaml
          resources:
            requests:
              cpu: "10m"
              memory: "32Mi"
            limits:
              cpu: "200m"
              memory: "64Mi"
```

Requests sit close to real usage, with some headroom. Limits are set noticeably higher, letting the app burst under real traffic without being capped too tightly, a form of overcommitting, more density, as long as not every Pod spikes at the exact same time.

### Apply it

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
```

## Setting the memory limit too low, on purpose

Wanted to see what actually happens when a limit is genuinely too small, not just read about it. Set memory down to `10Mi`, far below what Python and Flask need just to start.

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
kubectl get pods -n dev -w
```

The new Pod came up, immediately got killed, and kept getting killed.

```
nano-app-6c78558b9b-64vm4   0/1   OOMKilled          5 (32s ago)   3m57s
nano-app-6c78558b9b-64vm4   0/1   CrashLoopBackOff   5 (4s ago)    4m1s
```

`OOMKilled` is memory's version of hitting the ceiling, unlike CPU, which just throttles and slows down, memory has no "slow down" option, the kernel kills the container outright the moment it tries to use more than its limit allows.

## The part that mattered most, the site stayed up

While the new, broken Pod kept crash-looping, the 3 existing, healthy Pods from the previous version kept running and kept serving traffic the entire time.

```bash
curl http://dev.nano.local
```

The app responded normally throughout, Kubernetes never tore down the working Pods in favor of ones that couldn't even start, the readiness probe from Stage 10 was doing exactly its job here, the broken Pod never passed its readiness check, so it never received traffic, and the rollout correctly refused to fully proceed until the new version proved healthy.

## Fixing it

Restored sane values, back to the real numbers decided earlier.

```yaml
          resources:
            requests:
              cpu: "10m"
              memory: "32Mi"
            limits:
              cpu: "200m"
              memory: "64Mi"
```

```bash
kubectl apply -f dev/app/deployment.yaml -n dev
kubectl get pods -n dev
```

Everything settled back to `1/1 Running`, no more restarts.

## Postgres needed a different fix

Postgres runs as a bare Pod, not a Deployment, trying to apply the same resource change directly failed.

```
The Pod "postgres" is invalid: spec: Forbidden: pod updates may not change fields other than `spec.containers[*].image`...
```

A bare Pod can't have most fields updated in place, `resources` included, this is one of the real, practical limitations of bare Pods, and another reason Deployments exist, they handle exactly this by recreating Pods automatically. For Postgres, the fix was manual, delete then reapply.

```bash
kubectl delete pod postgres -n dev
kubectl apply -f dev/postgres/pod.yaml -n dev
```

Since the actual data lives on the PVC, not inside the Pod, deleting and recreating the Pod didn't lose anything, same proof as the very first persistence test back in Stage 4, the counter picked up exactly where it left off.

## Rolling it out everywhere

Applied the same requests and limits to `dev/postgres/pod.yaml`, `prod/app/deployment.yaml`, and `prod/postgres/pod.yaml`, each confirmed healthy afterward.

## Concepts learned

Requests are a reservation used for scheduling, limits are a hard ceiling actually enforced at runtime.
CPU over its limit gets throttled, slowed down, but kept alive. Memory over its limit gets the container killed outright, `OOMKilled`.
Setting resources too low doesn't make an app "lighter", it just guarantees it gets killed before it can even finish starting.
A healthy rollout, backed by readiness probes, protects existing good Pods even when a new version is completely broken.
Bare Pods can't have most fields, including resources, updated in place, they must be deleted and recreated, Deployments handle this automatically.
Choosing requests and limits should start from real observed usage (`kubectl top pod`), not arbitrary numbers.