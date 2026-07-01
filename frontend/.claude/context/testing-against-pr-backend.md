# Testing the Frontend Against an Unmerged Backend PR

When a backend PR adds or changes API behaviour, you can run that exact backend
locally — without checking out or building the API — and point your local
frontend dev server at it. CI publishes a Docker image for every PR.

## Where the images live

Every PR's CI builds and **pushes** multi-arch (amd64 + arm64) images to GHCR,
tagged `pr-<number>`. They are **public** — no `docker login` needed.

| Image | Tag | Contents |
| --- | --- | --- |
| `ghcr.io/flagsmith/flagsmith` | `pr-<number>` | Unified image — API + bundled frontend, serves on `:8000` |
| `ghcr.io/flagsmith/flagsmith-api` | `pr-<number>` | API only |

Use the **unified** image with the repo's root `docker-compose.yml`, which is
already wired for it (Postgres, migrations, API, task processor).

Confirm an image exists before relying on it:

```bash
docker manifest inspect ghcr.io/flagsmith/flagsmith:pr-<number> >/dev/null && echo pullable
```

## Run a PR backend + local frontend

From the repo root, create a one-off compose override that swaps the three
`flagsmith` services onto the PR image (the root compose hardcodes the image, so
an override file is the clean way to repoint it):

```bash
cat > docker-compose.pr.yml <<'EOF'
services:
  migrate-db:
    image: ghcr.io/flagsmith/flagsmith:pr-<number>
  flagsmith:
    image: ghcr.io/flagsmith/flagsmith:pr-<number>
  flagsmith-task-processor:
    image: ghcr.io/flagsmith/flagsmith:pr-<number>
EOF

docker compose -f docker-compose.yml -f docker-compose.pr.yml pull
docker compose -f docker-compose.yml -f docker-compose.pr.yml up
```

The API comes up on `localhost:8000`. Then run the frontend against it:

```bash
cd frontend
ENV=local npm run dev   # dev server on :3000, talks to the API on :8000
```

`docker-compose.pr.yml` is throwaway — delete it (or keep it git-ignored) when
done. To switch PRs, change the tag and re-run `pull` + `up`.

## Notes / gotchas

- **Flagsmith-on-Flagsmith gates.** Backend features are often gated by an
  OpenFeature flag (e.g. `feature_lifecycle`). The flag's default for a
  self-hosted/local run comes from the baked-in
  `api/integrations/flagsmith/data/environment.json`. Check it's enabled there;
  if not, the gated endpoints/fields won't appear.
- **Data, not just code.** Endpoints may need seeded data to return anything
  meaningful (e.g. code references, stale tags, usage). The image gives you the
  behaviour; you still have to create the data through the UI/API.
- **Inspect what the PR actually built.** Job logs show the pushed tag:
  `gh run view --job <id> --log | grep -i 'tags:'`. The `pr-<number>` convention
  is stable, but the logs are the source of truth.
- **Contract-checking without running.** To verify the frontend matches a
  backend PR's contract, read its diff directly instead of (or before) running:
  `gh api repos/Flagsmith/flagsmith/contents/<path>?ref=<pr-head-branch> --jq .content | base64 -d`.
