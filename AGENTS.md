Prioritise @AGENTS.local.md, if present.

Use British English.

# Tasks

Install Git hooks: `make install-hooks`
For backend code, read @api/README.md
For frontend code, read @frontend/README.md
For docs.flagsmith.com source, read @docs/README.md
For MCP code, read @mcp/README.md

# Code guidelines

These guidelines apply to all code in this repository.

## Comments

We use doc comments — docstrings in Python, TSDoc in TypeScript — for public functions and classes.

We avoid comments unless they reveal useful context only seen outside the code. When a comment is necessary, we prefer terse, one-line comments over long paragraphs.

We avoid deictic comments, such as references to a work session, or to an investigation. For example:
- "This fixes the failing test in CI" — deixis about a situation.
- "The cache was returning stale segments here" — deixis about a debugging session.
- "TODO: remove this logic branch before shipping to production" — deixis about team dynamics.
- "Decision 3: evaluate in the view" — deixis about a decision-making process.
- "Switched from offset pagination to cursors" — deixis about a prior draft.
- "We no longer recompute this on every request" — deixis about a discarded approach.

We prefer comments that survive the code across time, and that add value to future readers with no context. They reveal context as it is, never how the code came to be. For example:
- "Float sums drift on large totals."
- "Webhooks may arrive out of order."
- "Empty Content-Length is rejected upstream."
- "TODO: https://flagsmith.github.com/org/repo/issues/1234"
