# Docker Posgres DB migration to Pod

Old Postgres (Docker) keeps running the whole time, we only read from it. It has an export tool that prints the database as SQL text, the new Postgres has an import tool that can run that text. Your Mac bridges the two, since it can reach both.

```
old Postgres (Docker)    export as text    new Postgres (Pod)
```

### Step 1, export old database

```bash
docker exec postgres pg_dump -U nanouser nanostack > nanostack_dump.sql
```

Runs `pg_dump` inside the old container, saves the output to a file on the Mac.

### Step 2, sanity check the file

```bash
grep -i "visits" nanostack_dump.sql
```

Confirms the table and data sections exist. `pg_dump` uses `COPY ... FROM stdin` for data instead of `INSERT`, both work fine on import.

### Step 3, get the new database's password

```bash
kubectl get secret postgres-secret -n prod -o jsonpath='{.data.password}' | base64 -d
```

Pulls the password out of the Secret, base64 decoded to plain text.

### Step 4, import into new database

```bash
kubectl exec -i -n prod postgres -- env PGPASSWORD='PASSWORD-HERE' psql -U nanouser -d nanostack < nanostack_dump.sql
```

`-i` keeps input open so the file can be piped in. `env PGPASSWORD=...` avoids an interactive password prompt.

### Step 5, verify

```bash
kubectl exec -n prod postgres -- psql -U nanouser -d nanostack -c "SELECT * FROM visits;"
```

Runs one query directly, confirms the count matches.

### Notes

This is a one-time copy, not live sync, any visits between export and import create a small gap. Fine for a visitor counter, and for a real cutover you'd redo the export right before switching traffic.
Old stack stays running as a fallback until the app is proven working against the new database.