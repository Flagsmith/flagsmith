## Flagsmith Frontend

### Docker-based development

To bring up the API and database via Docker Compose:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

The application will bootstrap an admin user, organisation, and project for you. You'll find a link to set your password in your Compose logs:

```txt
Superuser "admin@example.com" created successfully.
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/.../...
```

### Local development

The project assumes the following tools installed:
- [Node.js](https://nodejs.org/) version 22.x
- [npm](https://www.npmjs.com/) version 10.x

To install dependencies, run `npm install`.

The API must be running on localhost:8000 (either via Docker or `make serve` in `../api`).

To bring up a dev server, run `ENV=local npm run dev`.

To run linters, run `npm run lint` (or `npm run lint:fix` to auto-fix).

To run type checking, run `npm run typecheck`.

### Environment configuration

Environment configuration is defined in `project_*.js` files (`common/project.js` for defaults, `env/project_*.js` for staging/prod/selfhosted), selected at build time based on the target environment. All configs support runtime overrides via `globalThis.projectOverrides`, allowing deployment-time customisation without rebuilding.

The `bin/env.js` script copies the appropriate `env/project_${ENV}.js` to `common/project.js`:
- `npm run dev` → copies `project_dev.js` (staging API)
- `ENV=local npm run dev` → copies `project_local.js` (localhost)
- `ENV=prod npm run bundle` → copies `project_prod.js` (production)

For a full list of frontend environment variables, see the [Flagsmith documentation](https://docs.flagsmith.com/deployment/hosting/locally-frontend#environment-variables).

### Code guidelines

#### Testing

This codebase uses TestCafe for end-to-end testing. Tests are located in the `e2e/` directory.

To run E2E tests (requires the API running on localhost:8000), run `npm run test`.

#### Typing

This codebase uses TypeScript. Run `npm run typecheck` to check for type errors.

We encourage adding types to new code and improving types in existing code when working nearby.

#### Design and architecture

The frontend is organised into:
- `common/` - Shared code (Redux store, RTK Query services, types, utilities)
- `web/components/` - React components
- `web/components/pages/` - Page-level components

State management uses Redux Toolkit with RTK Query for API calls. Services are defined in `common/services/`.

API types are centralised in:
- `common/types/requests.ts` - Request types
- `common/types/responses.ts` - Response types

For AI-assisted development, see [CLAUDE.md](https://github.com/Flagsmith/flagsmith/blob/main/frontend/CLAUDE.md).
