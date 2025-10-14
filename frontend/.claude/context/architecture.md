# Architecture & Configuration

## Monorepo Structure

Flagsmith is a monorepo with:
- `../api/` - Django REST API backend
- `/frontend/` - React frontend (current directory)
- Other packages in parent directory

## Environment Configuration

- Config file: `common/project.js` (base environment config)
- Contains API URL, environment settings, feature flag config
- Override with `.env` file in frontend directory
- Dev server: `npm run dev` (default) or `npm run dev:local` (local API)

## Key Technologies

- **React 16.14** + TypeScript + Bootstrap 5.2.2
- **Webpack 5** + Express dev server
- **Redux Toolkit + RTK Query** (API state management)
- **Flux stores** (legacy state management - being migrated to RTK)
- **Flagsmith SDK** (dogfooding - using own feature flag platform)
- **Sentry** (error tracking)
- **TestCafe** (E2E testing)

## State Management

### Modern (RTK Query)
- Base service: `common/service.ts`
- Store: `common/store.ts`
- Services: `common/services/use*.ts`
- Use `npx ssg` CLI to generate new services

### Legacy (Flux)
- Stores: `common/stores/*-store.js`
- Actions: `common/dispatcher/app-actions.js`
- Being gradually migrated to RTK Query

## Development Server

The frontend uses an Express middleware server (`/api/index.js`) that:
- Serves the Webpack dev bundle
- Provides server-side rendering for handlebars template
- Proxies API requests to Django backend

## Additional Rules

- **TypeScript**: Strict type checking enabled
- **ESLint**: Enforces import aliases (no relative imports)
- **Web-specific code**: Goes in `/web/` (not `/common/`)
- **Common code**: Shared utilities/types go in `/common/`
- **Redux Persist**: User data whitelist in `common/store.ts`

## Documentation

- Main docs: https://docs.flagsmith.com
- GitHub: https://github.com/flagsmith/flagsmith
