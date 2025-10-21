# CLAUDE.md

Flagsmith is a feature flag and remote config platform. This is the frontend React application.

## Monorepo Workflow

**IMPORTANT**: This is a monorepo. Backend and frontend are in the same repository.
- Get latest backend changes: `git merge origin/main` (NOT git pull in ../api)
- Backend: `../api/` (Django REST API)
- Frontend: `/frontend/` (React app - current directory)

## Quick Commands

**Development:**
- `npm run dev` - Start dev server (frontend + API middleware)
- `npm run dev:local` - Start with local environment config

**Code Quality:**
- `npx eslint --fix <file>` - Lint and fix a file (ALWAYS run on modified files)
- `npm run typecheck` - TypeScript type checking
- `npx lint-staged --allow-empty` - Lint all staged files

**Build:**
- `npm run bundle` - Production build

**Tools:**
- `npx ssg` - Generate RTK Query API services (optional)

## Slash Commands

- `/api` - Generate new RTK Query API service
- `/api-types-sync` - Sync TypeScript types with Django backend
- `/check` - Lint staged files
- `/context` - View available context files
- `/feature-flag` - Create a feature flag

## Directory Structure

```
/frontend/
  /common/          - Shared code (services, types, utils, hooks)
    /services/      - RTK Query API services (use*.ts files)
    /types/         - requests.ts & responses.ts (API types)
    store.ts        - Redux store + redux-persist
    service.ts      - RTK Query base config
  /web/             - Web-specific code
    /components/    - React components
    routes.js       - Application routing
  /e2e/             - TestCafe E2E tests
  /api/             - Express dev server middleware
  /env/             - Environment configs (project_*.js)
```

## Critical Rules

### 1. Imports - NO Relative Imports
```typescript
// ✅ Correct
import { service } from 'common/service'
import Button from 'components/base/forms/Button'

// ❌ Wrong
import { service } from '../../service'
import Button from '../base/forms/Button'
```

### 2. Linting - ALWAYS Required
- Run `npx eslint --fix <file>` on ANY file you modify
- Pre-commit hooks use lint-staged

### 3. Forms - NO Formik/Yup
This codebase uses **custom form components**, NOT Formik or Yup:
```typescript
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
// Use state + custom validation
```

### 4. Modals - NEVER use window.confirm
```typescript
// ✅ Correct
import { openConfirm } from 'components/base/Modal'
openConfirm({ title: 'Delete?', body: '...', onYes: () => {} })

// ❌ Wrong
window.confirm('Delete?')
```

### 5. API Integration
- Backend types sync: Run `/api-types-sync` before API work
- RTK Query services: `common/services/use*.ts`
- Manual service creation or use `npx ssg` (optional)
- Check Django backend in `../api/` for endpoint details

### 6. State Management
- **RTK Query**: API calls & caching (`common/service.ts`)
- **Redux Toolkit**: Global state (`common/store.ts`)
- **Flux stores**: Legacy (in `common/stores/`)

### 7. Feature Flags (Dogfooding!)
This **IS** Flagsmith - the feature flag platform itself. We dogfood our own SDK:
```typescript
import flagsmith from 'flagsmith'
// Check .claude/context/feature-flags.md
```

### 8. Type Organization
- Extract inline union types to named types:
```typescript
// ✅ Good
type Status = 'active' | 'inactive'
const status: Status = 'active'

// ❌ Avoid
const status: 'active' | 'inactive' = 'active'
```

## Tech Stack
- **React**: 16.14 (older version, not latest)
- **TypeScript**: 4.6.4
- **State**: Redux Toolkit + RTK Query + Flux (legacy)
- **Styling**: Bootstrap 5.2.2 + SCSS
- **Build**: Webpack 5 + Express dev server
- **Testing**: TestCafe (E2E)

## Context Files

Detailed documentation in `.claude/context/`:
- `api-integration.md` - RTK Query patterns, service creation
- `api-types-sync.md` - Django ↔ TypeScript type syncing
- `architecture.md` - Environment config, project structure
- `feature-flags.md` - Flagsmith SDK usage (dogfooding)
- `forms.md` - Custom form patterns
- `git-workflow.md` - Git workflow, linting, pre-commit
- `patterns.md` - Code patterns, error handling
- `ui-patterns.md` - Modals, confirmations, UI helpers

