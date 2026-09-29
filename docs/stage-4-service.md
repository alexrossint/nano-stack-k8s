# The Service

## **The problem it solves**

A Pod's IP is temporary. If Postgres crashes and Kubernetes recreates it, the new Pod gets a **new IP**. Anything that saved the old IP breaks. On Docker you avoided this with container names on a shared network. Kubernetes needs the same fix, at cluster scale.

Think of it like an F5 VIP. Clients (or here, our app) hit the VIP, F5 picks a real pool member behind it, and members can change without clients noticing. A Service does the same for Pods.

## **What a Service does**

It's a stable name and IP that sits in front of one or more Pods. Other Pods talk to the Service, and the Service always forwards to whichever real Pods are alive right now.

```
app  →  talks to  →  Service name "postgres"  →  forwards to  →  the current Postgres Pod
```

The name never changes, even if the Pod behind it does.

## **Service types**

#### ClusterIP

The default type. Gives an internal-only address, reachable only from inside the cluster. Postgres uses this, since only the app should reach it.

#### NodePort

Also opens a port on the node itself, so something outside the cluster can reach it too, using the node's own IP. Useful when a Pod needs to be reached from your Mac's browser.

#### LoadBalancer

Asks the cloud provider to create a real external load balancer, with its own public IP, in front of the Service. It's the type used for public-facing apps on a cloud platform.

## **DNS, automatically**

Kubernetes runs its own internal DNS. Any Service gets a name that other Pods in the same namespace can just use directly, like `postgres`. Cross-namespace, it's `postgres.prod.svc.cluster.local`, but inside `prod` the short name works, same as the container name did on `nano-net`.

## **What the Service file will contain**

```
which Pods to send traffic to   →  selector: app: postgres
which port to listen on         →  5432
which port to forward to        →  5432 on the Pod
```

Ports can differ on each side, but for Postgres they'll match.

**What changes for the app later**

`DB_HOST=postgres` stays exactly the value it was in Docker. Only what's behind that name changed, from a container name to a Service name.

## **How it finds the right Pods**

Through the label we already set: `labels: app: postgres` on the Pod. 

The Service doesn't point at a Pod by name. It has a **selector**, `app: postgres`, and it automatically picks up any Pod carrying that label. 

If the Pod is deleted and a new one appears with the same label, the Service finds it without you touching anything. This is why labels matter, they're the glue.

#### Creating the `service.yaml`  file

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

`selector: app: postgres` is the pool-matching rule, it grabs any Pod carrying that label.
`port` is the Service's own port (the VIP port).
`targetPort` is the port it forwards to on the Pod.

#### Describe pod:

```bash
nano-stack-k8s % kdp -n prod
Name:             postgres
Namespace:        prod
Priority:         0
Service Account:  default
Node:             colima/192.168.5.1
Start Time:       Mon, 28 Sep 2026 20:44:52 +0300
**Labels:           app=postgres**
Annotations:      <none>
Status:           Running
IP:               10.42.0.6
```

<aside>
💡

Labels are just tags

`app=postgres` on a Pod is like tagging a VM `role=webserver`. If we later scale to 3 Postgres Pods, all 3 carry the same label, and the Service picks up all 3 automatically. One Service works no matter how many Pods sit behind it, same as one F5 VIP can have many pool members.

</aside>

#### Apply it

bash

```bash
kubectl apply -f k8s/postgres/service.yaml -n prod
```

#### Check it

bash

```bash
kubectl get svc -n prod
```

Shows the VIP (CLUSTER-IP) and port.

bash

```bash
kubectl describe svc postgres -n prod
```