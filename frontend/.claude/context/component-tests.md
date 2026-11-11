# Component tests

Jest runs in `node` by default. A component test opts into the DOM with a docblock at the top of the file:

```tsx
/**
 * @jest-environment jsdom
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
```

Put tests in `__tests__/` next to the component, named `ComponentName.test.tsx`. SCSS imports are mocked in `jest.config.js`, and jest-dom matchers (`toBeInTheDocument`) are loaded in `jest.setup.ts`.

## Rules

1. **Test what a user or caller relies on.** Find elements by role and accessible name (`getByRole('checkbox', { name: 'Production' })`), act with `userEvent`, assert on what they see or on the callbacks they passed. No class names, no snapshots, no `data-test`, no reaching into state.
2. **Every test must fail when its behaviour breaks.** Before committing, break the code once (drop the handler, flip the condition) and watch the test go red. A test that stays green is deleted, not kept.
3. **Only components with logic or states get component tests.** Pure layout is covered by Storybook stories and Chromatic.
4. **Helpers are tested through inputs and outputs**, in plain `.test.ts` files without the DOM.
5. **One test per behaviour.** The name states the behaviour (`removes without also clicking the chip`), not the implementation.

If a role query can't find an element, fix the component's semantics instead of adding a test id.
