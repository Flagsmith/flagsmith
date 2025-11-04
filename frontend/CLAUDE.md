# CLAUDE.md

## Commands
- `npm run dev` - Start dev server
- `npm run typecheck` - Type checking

## Structure
- `/common` - Shared Redux/API (no web/mobile code)
- `/web/components` - React components (includes `/web/components/pages/` for all page components)
- `/web/components/pages/` - **All page components** (e.g., `FeaturesPage.js`, `ProjectSettingsPage.js`)
- `/common/types/` - `requests.ts` and `responses.ts` for API types
- Ignore: `ios/`, `android/`, `.net/`

## Rules
1. **API Integration**: Use `npx ssg` CLI + check `../hoxtonmix-api` backend
2. **Forms**: Yup + Formik + `validateForm` utility (see `/examples/forms/`)
3. **Imports**: Use `common/`, `components/`, `project/` (NO relative imports)
4. **State**: Redux Toolkit + RTK Query, store in `common/store.ts`
5. **Feature Flags**: When user says "create a feature flag", you MUST: (1) Create it in Flagsmith using MCP tools (`mcp__flagsmith__create_feature`), (2) Implement code with `useFlags` hook. See `.claude/context/feature-flags.md` for details
6. **Linting**: ALWAYS run `npx eslint --fix <file>` on any files you modify
7. **Type Enums**: Extract inline union types to named types (e.g., `type Status = 'A' | 'B'` instead of inline)
8. **NO FETCH**: NEVER use `fetch()` directly - ALWAYS use RTK Query mutations/queries (inject endpoints into services in `common/services/`), see api-integration context

## Key Files
- Store: `common/store.ts`
- Base service: `common/service.ts`
- Forms example: `/examples/forms/ComprehensiveFormExample.tsx`

## Context Files

The `.claude/context/` directory contains **required patterns and standards** for this codebase. These are not optional suggestions - they document how things must be done in this project.

For detailed guidance on specific topics:
- **Quick Start**: `.claude/context/quick-reference.md` - Common tasks, commands, patterns
- **API Integration**: `.claude/context/api-integration.md` - Adding endpoints, RTK Query (required reading for API work)
- **Backend**: `.claude/context/backend-integration.md` - Finding endpoints, backend structure
- **UI Patterns**: `.claude/context/ui-patterns.md` - Tables, tabs, modals, confirmations (required reading for UI work)
- **Feature Flags**: `.claude/context/feature-flags.md` - Using Flagsmith flags (optional, only when requested)
- **Code Patterns**: `.claude/context/patterns.md` - Complete examples, best practices
- **Forms**: `.claude/context/forms.md` - Yup + Formik patterns

**Tip:** Start with `quick-reference.md` for common tasks and checklists.
