---
description: Run type checking and linting on staged files
---

Run TypeScript checking and linting on all currently staged files, similar to pre-commit hooks. Steps:
1. Run `npm run check:staged` to typecheck and lint only staged files
2. Report any type errors or linting issues found
3. If errors exist, offer to fix them
