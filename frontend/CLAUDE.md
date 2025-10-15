# CLAUDE.md

## Commands
- `npm run dev` - Start dev server (frontend + API middleware)
- `npm run dev:local` - Start dev server with local environment
- `npx ssg help` - Generate Redux/API hooks (REQUIRED for API)
- `npm run typecheck` - Type checking (all files)
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Auto-fix ESLint issues
- `npm run bundle` - Build production bundle
- `/check` - Slash command to typecheck and lint

## Monorepo Structure
- `../api/` - Django REST API backend
- `/frontend/` - React frontend (current directory)
  - `/common/` - Shared code (services, types, utils, hooks)
  - `/web/` - Web-specific code (components, pages, styles)
  - `/e2e/` - TestCafe E2E tests
  - `/api/` - Express middleware server

## Key Directories
- `/common/services/` - RTK Query services (use*.ts files)
- `/common/types/` - `requests.ts` and `responses.ts` for API types
- `/web/components/` - React components
- `/web/routes.js` - Application routing

## Rules
1. **API Integration**: Use `npx ssg` CLI to generate RTK Query services
   - Check `../api/` Django backend for endpoint details
   - Use `/backend <search>` slash command to search backend
2. **Forms**: Custom form components (NO Formik/Yup in this codebase)
   - Use InputGroup, Input, Select components from global scope
   - See existing forms in `/web/components/` for patterns
3. **Imports**: Use `common/*`, `components/*`, `project/*` (NO relative imports - enforced by ESLint)
4. **State**: Redux Toolkit + RTK Query + Flux stores (legacy)
   - Store: `common/store.ts` (RTK)
   - Legacy stores: `common/stores/` (Flux)
5. **Feature Flags**: This IS Flagsmith - the feature flag platform itself
   - Uses own Flagsmith SDK internally for dogfooding
   - SDK imported as `flagsmith` package
6. **Patterns**: See `.claude/context/patterns.md` for common code patterns

## Key Files
- Store: `common/store.ts` (RTK + redux-persist)
- Base service: `common/service.ts` (RTK Query base)
- Project config: `common/project.js` (environment config)
- Routes: `web/routes.js`

## Tech Stack
- React 16.14 + TypeScript
- Redux Toolkit + RTK Query (API state)
- Flux stores (legacy state management)
- Bootstrap 5.2.2 + SCSS
- Webpack 5 + Express dev server
- TestCafe (E2E tests)

For detailed guidance, see `.claude/context/` files.
