# Stage 15, CI/CD: build, deploy and roll back automatically

Every release was still typed by hand: build the image, pick a tag, run `helm upgrade`, roll back if something broke. One wrong tag, 2.7 typed and 2.1 built, cost real time to find. In Stage 11 the rollout history had no reason for any change, and we parked that for here. This stage makes a push to GitHub do all of it, check that the app answers, wait for approval before touching prod, and undo the release by itself if the check fails.

## Step 1, put a runner on the Mac

GitHub's own runners are machines on the internet and can't reach a cluster living on a laptop. A self-hosted runner is an agent installed on the Mac. It connects out to GitHub, asks for jobs, and runs them locally, where Docker and the cluster already are.

In the repo, Settings, Actions, Runners, New self-hosted runner, macOS, ARM64. The page shows the download commands and a `./config.sh --url ... --token ...` command with a current version and a token that expires within an hour, so copy them from there. Pressing Enter for the defaults is fine.

The runner folder lives next to the repo, not inside it. It holds credentials, and a public repo must never contain them.

### Start it

```bash
./run.sh
```

It prints `Listening for Jobs`, and the runner shows as `Idle` in GitHub. The terminal has to stay open.

### Prove it with a test workflow

Created `.github/workflows/test-runner.yml` in the repo root. GitHub only reads workflow files from that exact folder.

```yaml
name: test-runner
on: workflow_dispatch
jobs:
  test:
    runs-on: self-hosted
    steps:
      - run: hostname
      - run: docker version
      - run: kubectl get nodes
```

`workflow_dispatch` adds a Run workflow button in the Actions tab. The job ran on the Mac and printed the hostname, the Docker version, and the node as `Ready`.

## Step 2, the build job

Created `.github/workflows/ci.yaml`. It starts on a push to `main` that changes something inside `app/`, or from the Run workflow button.

```yaml
on:
  push:
    branches: [main]
    paths: ['app/**']
  workflow_dispatch:
```

The first step downloads the repo into the runner's work folder, because every job starts with an empty folder.

```yaml
      - uses: actions/checkout@v6
```

The image is tagged with the short commit ID, so every build gets a unique tag and the tag always says which code is inside. `$( )` puts the command's output into the tag.

```yaml
      - name: Build image
        run: docker build -t nano-stack-app:$(git rev-parse --short HEAD) ./app
```

## Step 3, deploy to dev from the values file

The new tag is written into `values-dev.yaml`, and `helm upgrade` reads it from there. This keeps the tag in the values file instead of on the command line. On macOS, `sed -i` needs the empty `''` after it.

```yaml
      - name: Write the new tag into values-dev.yaml
        run: sed -i '' "/tag:/s/\".*\"/\"$(git rev-parse --short HEAD)\"/" nano-stack/values-dev.yaml
```

The deploy stores a readable reason with each Helm revision: the commit ID and the first line of the commit message. This replaces the empty `CHANGE-CAUSE` from Stage 11. The command sits in a `run: |` block, because the `: ` inside the description makes YAML read it as a new key.

```yaml
      - name: Deploy to dev
        run: |
          helm upgrade nano-stack nano-stack/ -n dev -f nano-stack/values-dev.yaml --description "$(git rev-parse --short HEAD): $(git log -1 --pretty=%s)"
```

### Check it

```bash
helm history nano-stack -n dev
```

The newest revision reads like `743970a: Changed icon`.

## Step 4, check that the app answers

The rollout step waits until the new Pods are ready and fails after 120 seconds. Without it, the curl could hit the old Pods before the rollout finishes.

```yaml
      - name: Wait for rollout
        run: kubectl rollout status deployment/nano-app -n dev --timeout=120s
```

The smoke test requests the page. `-f` makes curl fail on error codes such as 503, `-s` hides the progress bar, and `-S` still prints an error message.

```yaml
      - name: Smoke test
        run: curl -fsS http://dev.nano.local
```

If either step fails, the run turns red and the next step is skipped.

## Step 5, commit the new tag back to Git

The edit to `values-dev.yaml` exists only in the runner's work folder. Without a commit, Git would no longer match the cluster. The step runs last, so a failed deploy never gets recorded. The job needs write permission, set above `jobs:`.

```yaml
permissions:
  contents: write
```

```yaml
      - name: Commit the new tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add nano-stack/values-dev.yaml
          git diff --staged --quiet && exit 0
          git commit -m "Deploy $(git rev-parse --short HEAD) to dev"
          git push origin HEAD:main
```

A push made by the pipeline itself doesn't start another run. GitHub blocks that when the built-in token is used.

GitHub now holds a commit the Mac doesn't, so every pipeline run is followed by a pull. Making rebase the default keeps a plain pull working:

```bash
git config --global pull.rebase true
```

```bash
git pull
```

## Step 6, deploy to prod behind an approval

In GitHub, Settings, Environments, New environment, named `production`, with Required reviewers set to the owner. This is the approve button.

A second job in the same file waits for the dev job, then waits for the click.

```yaml
  deploy-prod:
    needs: build-and-deploy
    runs-on: self-hosted
    environment: production
    steps:
      - uses: actions/checkout@v6
        with:
          ref: main
```

`needs` starts the job only after dev is green. `environment: production` pauses it until a reviewer clicks Review deployments, then Approve. `ref: main` checks out the latest `main`, which already holds the dev job's commit, so the final push isn't rejected.

Prod deploys the same image dev built. `github.sha` is the full commit ID, and `cut -c1-7` shortens it to the 7 characters the dev job used.

```yaml
      - name: Write the new tag into values-prod.yaml
        run: sed -i '' "/tag:/s/\".*\"/\"$(echo ${{ github.sha }} | cut -c1-7)\"/" nano-stack/values-prod.yaml

      - name: Deploy to prod
        run: |
          helm upgrade nano-stack nano-stack/ -n prod -f nano-stack/values-prod.yaml --description "$(echo ${{ github.sha }} | cut -c1-7): promoted from dev"

      - name: Wait for rollout
        run: kubectl rollout status deployment/nano-app -n prod --timeout=120s

      - name: Smoke test
        run: curl -fsS http://prod.nano.local
```

## Step 7, roll back automatically

`if: failure()` makes a step run only when an earlier step in the job failed. The rollback puts the previous revision of the release back.

```yaml
      - name: Roll back if anything failed
        if: failure()
        run: helm rollback nano-stack -n prod

      - name: Commit the new tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add nano-stack/values-prod.yaml
          git diff --staged --quiet && exit 0
          git commit -m "Deploy ${{ github.sha }} to prod"
          git push origin HEAD:main
```

The commit step comes after the rollback and runs only on success, so a failed prod deploy never reaches Git.

### The full [ci.yaml]
``` yaml
name: CI

on:
  push:
    branches: [main]
    paths: ['app/**']
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v6

      - name: Build image
        run: docker build -t nano-stack-app:$(git rev-parse --short HEAD) ./app

      - name: Write the new tag into values-dev.yaml
        run: sed -i '' "/tag:/s/\".*\"/\"$(git rev-parse --short HEAD)\"/" nano-stack/values-dev.yaml

      - name: Deploy to dev
        run: |
          helm upgrade nano-stack nano-stack/ -n dev -f nano-stack/values-dev.yaml --description "$(git rev-parse --short HEAD): $(git log -1 --pretty=%s)"

      - name: Wait for rollout
        run: kubectl rollout status deployment/nano-app -n dev --timeout=120s

      - name: Smoke test
        run: curl -fsS http://dev.nano.local

      - name: Commit the new tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add nano-stack/values-dev.yaml
          git diff --staged --quiet && exit 0
          git commit -m "Deploy $(git rev-parse --short HEAD) to dev"
          git push origin HEAD:main
  deploy-prod:
    needs: build-and-deploy
    runs-on: self-hosted
    environment: production
    steps:
      - uses: actions/checkout@v6
        with:
          ref: main

      - name: Write the new tag into values-prod.yaml
        run: sed -i '' "/tag:/s/\".*\"/\"$(echo ${{ github.sha }} | cut -c1-7)\"/" nano-stack/values-prod.yaml

      - name: Deploy to prod
        run: |
          helm upgrade nano-stack nano-stack/ -n prod -f nano-stack/values-prod.yaml --description "$(echo ${{ github.sha }} | cut -c1-7): promoted from dev"

      - name: Wait for rollout
        run: kubectl rollout status deployment/nano-app -n prod --timeout=120s

      - name: Smoke test
        run: curl -fsS http://prod.nano.local

      - name: Roll back if anything failed
        if: failure()
        run: helm rollback nano-stack -n prod

      - name: Commit the new tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add nano-stack/values-prod.yaml
          git diff --staged --quiet && exit 0
          git commit -m "Deploy ${{ github.sha }} to prod"
          git push origin HEAD:main
```
### Prove the rollback

Temporarily changed the prod smoke test URL to `http://prod.nano.local/nothing`, which returns a 404. After approving the deploy, the log showed:

```
curl: (22) The requested URL returned error: 404
Error: Process completed with exit code 22.
Rollback was a success! Happy Helming!
```

The job failed, the rollback ran, and the prod page still worked. Then the URL was changed back to `http://prod.nano.local`.

```bash
helm history nano-stack -n prod
```

## Gotchas hit along the way

The first push of a workflow file was rejected, because a token with only the `repo` scope can't change workflow files. Adding the `workflow` scope to the existing token fixed it, and the saved Keychain password kept working.

The job failed with `failed to connect to the docker API`. Colima had stopped, so its Docker socket didn't exist. The first thing to check is `colima status`.

A warning said Node.js 20 is deprecated. The checkout action was on `v4`, and `v6` runs on Node 24.

The runner folder was first inside the repo, and VS Code showed 9319 files to commit. `git reset` cleared the staging area, and moving the folder out of the repo fixed it. Nothing had been committed.

The push was rejected, and `git pull` said the branches had diverged. The pipeline's own commit had landed on GitHub first. `git pull --rebase` put the local commit on top.

A manual run shows a different description than a push. A click on Run workflow checks out the latest commit on `main`, which can be the pipeline's own commit, so the description shows its message.

## Concepts learned

A runner is an agent that asks GitHub for jobs, the same way a backup agent asks its server. It connects out, so the Mac needs no open port.

A workflow file describes the job, and the runner only executes it. GitHub reads workflows only from `.github/workflows/` in the repo root.

An image tagged with the commit ID needs no version bump by hand, and `git show` on the tag shows the exact code inside.

Helm revisions can carry a reason with `--description`, so `helm history` reads like a changelog.

A failed step skips every normal step after it, which is why the Git commit comes last. `if: failure()` is the exception, and runs only after a failure.

An environment with a required reviewer pauses a job until someone approves it.

The pipeline writes to the same branch a person pushes to, so a pull comes before every push. Teams that want to avoid this pass the tag on the command line, or keep deployment tags in a separate repository that only the pipeline writes to.

## What stays outside the pipeline

The namespaces, `postgres-secret` in each namespace, the nginx ingress controller, and the lines in `/etc/hosts`.