# Architecture & Configuration

## Environment & Whitelabelling

- Config files: `common/env/project_<ENV>_<NAME>.js`
- `ENV`: `dev` or `prod` (default: `dev`)
- `NAME`: Brand name like `hoxtonmix-portal` (default: `hoxtonmix-portal`)
- Override: `API_URL=https://my-api.com/api/v1/ npm run dev`

## Key Technologies

- Next.js 13.1.5 + TypeScript + Bootstrap 5.3.3
- Preact (aliased as React for smaller bundle)
- AWS Amplify (Cognito auth)
- Sentry (error tracking)
- Flagsmith (feature flags - see `feature-flags.md` for usage)

## Additional Rules

- **TypeScript/ESLint**: Build ignores errors (`ignoreBuildErrors: true`)
- **Web-specific utilities**: Go in `/project/` (not `/common`)
- **Redux Persist**: Whitelist in `common/store.ts`
- **Layout**: Default in `pages/_app.tsx` (`<Aside>` + `<Nav>`), override with `getLayout` pattern

## Documentation

External docs: https://www.notion.so/hoxtonmix/Public-Website-and-Portal-77ae32dba39b42fb869cb18d18a73cf5
