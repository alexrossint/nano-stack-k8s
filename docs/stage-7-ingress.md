# Stage 7, Expose the app with Ingress

NodePort worked, but it ties clients to raw port numbers, cluster-wide, easy to run out of, not something you'd actually hand to real users. Ingress replaces that with real hostnames instead, one clean entry point per app.

## Step 1, install an Ingress controller

The cluster didn't have one by default, confirmed with

```bash
kubectl get ingressclass
```

Empty output, nothing registered. Installed nginx-ingress, the most common choice in real jobs, using the official manifest

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/cloud/deploy.yaml
```

Creates its own namespace, `ingress-nginx`, deploys the controller Pod plus two one-time setup Jobs.

### Check it

```bash
kubectl get pods -n ingress-nginx
```

`ingress-nginx-controller` shows `Running`, the two admission Jobs show `Completed`, their correct final state, not an error.

```bash
kubectl get ingressclass
```

Now shows `nginx`, confirming the controller registered itself.

## Step 2, understand what's actually running

k3s also creates a small helper Pod automatically, `svclb-ingress-nginx-controller`, in `kube-system`, with two containers, `lb-tcp-80` and `lb-tcp-443`. These are simple pass-through proxies, they just forward whatever arrives on the node's port 80 or 443 straight into the real controller Pod, no routing logic themselves. On a real multi-node cluster, a cloud LoadBalancer would do this job, k3s fakes it locally.

The actual routing decisions happen inside `ingress-nginx-controller` itself, once it has rules to follow.

## Step 3, write the Ingress rule

Created the file, `k8s/app/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nano-app
spec:
  ingressClassName: nginx
  rules:
    - host: dev.nano.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nano-app
                port:
                  number: 5000
```

`ingressClassName: nginx` tells it which installed controller handles this.
`host` is the hostname this rule matches, requests claiming to be for anything else are ignored by this rule.
`path: /` with `pathType: Prefix` matches every URL under that hostname.
`backend.service` points to the existing `nano-app` Service, same port number (`5000`) the Service itself already listens on, nothing new is opened, Ingress just references what already exists.

### Apply it, dev

```bash
kubectl apply -f k8s/app/ingress.yaml -n dev
```

Same file reused for prod, only the `host` value changes, `prod.nano.local` instead of `dev.nano.local`.

### Apply it, prod

```bash
kubectl apply -f k8s/app/ingress.yaml -n prod
```

### Check it

```bash
kubectl get ingress -n dev
kubectl get ingress -n prod
```

Shows `nano-app`, class `nginx`, the correct hostname, listening on port `80`.

## Step 4, fake DNS locally

No real DNS server exists in this lab, so hostnames are resolved manually using the Mac's hosts file.

```bash
sudo nano /etc/hosts
```

Added

```
127.0.0.1 dev.nano.local
127.0.0.1 prod.nano.local
```

Colima forwards traffic to the Mac's `localhost` automatically, same behavior already seen with NodePort earlier.

## Step 5, test it

```bash
curl http://dev.nano.local
curl http://prod.nano.local
```

Both returned the app's page, each showing its own namespace's counter, confirming the full path works end to end, hostname resolved, caught by the node's proxy, routed by the controller, through the Service, into the right Pod.

## Full traffic path

```
Mac resolves hostname to an IP, via /etc/hosts
request hits port 80 on the node
lb-tcp-80 forwards it untouched
ingress-nginx-controller reads its rules, matches the hostname
routes to the matching Service, in the matching namespace
Service picks one of its matching Pods
```

## On-prem comparison

Like an F5 with multiple virtual servers, one listener, routing to different pools based on hostname, instead of one VIP per application.