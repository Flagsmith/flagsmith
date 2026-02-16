# Git Workflow

## Pre-Commit Checking Strategy

Before creating commits, always check and lint staged files to catch errors early:

```bash
npm run check:staged
```

Or use the slash command:
```
/check-staged
```

This runs both typechecking and linting on staged files only, mimicking pre-commit hooks.

## Available Scripts

- `npm run check:staged` - Typecheck + lint staged files (use this!)
- `npm run typecheck:staged` - Typecheck staged files only
- `npm run lint:staged` - Lint staged files only (with --fix)

## Important Notes

- Never run `npm run typecheck` (full project) or `npm run lint` on all files unless explicitly requested
- Always focus on staged files only to keep checks fast and relevant
- The lint:staged script auto-fixes issues where possible
- Fix any remaining type errors or lint issues before committing
