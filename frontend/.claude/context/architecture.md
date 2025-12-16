# Architecture & Configuration

## Environment Configuration

- Config files: `env/project_<ENV>.js`
- Available environments: `dev`, `prod`, `staging`, `local`, `selfhosted`, `e2e`
- Project config: `common/project.js` (imports from env files)
- Override: `ENV=local npm run dev` or `ENV=staging npm run dev`

## Key Technologies

- React 16.14 + TypeScript + Bootstrap 5.2.2
- Redux Toolkit + RTK Query (API state management)
- Flux stores (legacy state management)
- Webpack 5 + Express dev server
- Sentry (error tracking)
- Flagsmith (feature flags - this project IS Flagsmith, dogfooding its own platform)

## Additional Rules

- **TypeScript/ESLint**: Build may ignore some errors, but always run linting on modified files
- **Web-specific code**: Goes in `/web/` directory (not `/common`)
- **Redux Persist**: Whitelist in `common/store.ts`
- **Imports**: Always use path aliases (`common/*`, `components/*`, `project/*`) - NO relative imports

## Documentation

Check the main repository README and docs for additional information
