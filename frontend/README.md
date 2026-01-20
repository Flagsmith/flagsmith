## Flagsmith Frontend

TODO

## E2E Testing

### Docker E2E Image

The E2E tests run in a Docker container (`Dockerfile.e2e`) that automatically installs Playwright and Firefox during the build. The Firefox version is automatically matched to the Playwright version in `package.json`, ensuring compatibility.

When you update Playwright in `package.json`, the next Docker build will automatically use the correct Firefox version - no manual intervention required.
