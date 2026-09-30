# Stage 6, Database migration and cutover

With prod's Postgres and app Pod proven working in Kubernetes, this stage moves the real data over from the old Docker setup, then switches off the old containers for good.

## Step 1, export the current data from the old Docker Postgres

The old stack keeps running the whole time up to this point, we only read from it, nothing is stopped yet.

### Export it

```bash
docker exec postgres pg_dump -U nanouser nanostack > nanostack_dump.sql
```

Runs `pg_dump` inside the old Docker container, saves the output as SQL text to a file on the Mac.

### Check it

```bash
grep -i "visits" nanostack_dump.sql
```

Confirms the table and its data section are present in the file.

## Step 2, get prod's database password

The new database in Kubernetes is secured with a Secret, its password needs to be read out before we can log in and import anything.

```bash
kubectl get secret postgres-secret -n prod -o jsonpath='{.data.password}' | base64 -d
```

Pulls the password field from the Secret, decodes it from base64 to plain text.

## Step 3, import the data into prod's Postgres Pod

```bash
kubectl exec -i -n prod postgres -- env PGPASSWORD='PASSWORD-HERE' psql -U nanouser -d nanostack < nanostack_dump.sql
```

`-i` keeps input open so the dump file can be piped in.
`env PGPASSWORD=...` supplies the password without an interactive prompt.

## Step 4, verify the counts match

```bash
kubectl exec -n prod postgres -- psql -U nanouser -d nanostack -c "SELECT * FROM visits;"
```

Runs a direct query against prod's new database, confirms the counter matches what the old Docker app was last showing.

## Step 5, stop sending traffic to the old stack

With prod's app already tested and serving correctly through its own Service, this is the actual cutover moment, from here on `nano-app` in Kubernetes is the real app, not the Docker one.

## Step 6, stop the old Docker containers

```bash
docker stop nano-app postgres
```

Stops both old containers without deleting them, they can still be started again quickly if a rollback is ever needed. The Docker volume (`nano-pgdata`) is untouched either way. Once prod in Kubernetes has been trusted for a while, they can be removed properly.


## Outcome

```
old Docker stack    stopped, not removed, kept as a fallback
prod (Kubernetes)    the real app, real data, fully migrated
dev (Kubernetes)     still isolated, still its own separate database
```