# Visual check

Turns Playwright snapshot comparisons into a GitHub check with Before / After / Diff images for every changed screenshot, so reviewers see visual changes without downloading the report.

- No changes: the check passes with "No visual changes (N compared)".
- Changes: the check is `neutral` and lists each changed or new screenshot with its images.

It has no dependencies: plain Node (20+) and the GitHub REST API.

## Usage

Add Playwright's JSON reporter to the config that runs your snapshot comparisons:

```ts
reporter: [['json', { outputFile: 'visual-results/report.json' }]],
```

Then, after that run:

```yaml
permissions:
  contents: write # commits the images to the images branch
  checks: write

steps:
  - uses: ./.github/actions/visual-check
    with:
      report: visual-results/report.json
```

| Input | Default | |
| --- | --- | --- |
| `report` | | Path to the Playwright JSON report |
| `root-dir` | | Local directory matching the report's `rootDir`, when Playwright ran elsewhere (e.g. a container) |
| `report-url` | | Link to the full report |
| `check-name` | `Visual regression` | |
| `images-branch` | `visual-check-images` | |
| `mode` | `report` | `cleanup` prunes images of closed pull requests |

Outputs: `changed`, `added`, `total`, `check-url`.

## How images are shown

GitHub only renders images from URLs, so the action commits the changed screenshots to `images-branch` and links them by commit. Run it with `mode: cleanup` on a schedule: it keeps only open pull requests' images and squashes the branch history, so the branch never grows.

## Limitations

- Public repositories only: GitHub can't render raw images of private ones in a check.
- Pull requests from forks get a read-only token, so they only get the job summary.

## Tests

```sh
node --test .github/actions/visual-check/test/*.test.mjs
```
