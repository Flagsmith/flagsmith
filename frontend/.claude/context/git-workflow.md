# Git Workflow

## Pre-Commit Checking Strategy

Before creating commits, always lint staged files to catch errors early:

```bash
npx lint-staged --allow-empty
```

Or use the slash command:
```
/check
```

This runs ESLint with auto-fix on staged files only, mimicking pre-commit hooks.

## Available Scripts

- `npm run lint` - Lint all files
- `npm run lint:fix` - Lint and auto-fix all files
- `npm run typecheck` - Run TypeScript type checking
- `npx lint-staged --allow-empty` - Lint staged files only (use before committing!)

## Linting Configuration

The project uses lint-staged with the following configuration:
- Runs on `*.{js,tsx,ts}` files
- Uses `suppress-exit-code eslint --fix` to auto-fix issues
- Configured in `package.json` under `lint-staged` key

## Important Notes

- Always run linting on modified files: `npx eslint --fix <file>`
- The lint-staged script auto-fixes issues where possible
- Fix any remaining lint issues before committing
- Husky pre-commit hooks may run lint-staged automatically
