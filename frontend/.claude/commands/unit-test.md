---
description: Analyse a frontend file and generate unit tests (Jest)
---

Generate unit tests for the frontend file at `$ARGUMENTS`.

**Note:** This command is for frontend code only. For backend (Python) tests, see `../api/README.md`.

## Steps

1. **Check for existing tests**
   - Look for `__tests__/{filename}.test.ts` in the same directory
   - If tests exist, analyse them for coverage gaps

2. **Read and analyse the source file**
   - Identify all exported functions, classes, and constants
   - Note dependencies and imports
   - Determine testability:
     - Pure functions (no side effects) → highly testable
     - React components → may need mocking
     - Functions with external dependencies → note what needs mocking

3. **Generate test file**
   - Follow the pattern in `common/utils/__tests__/format.test.ts`
   - Location: `{sourceDir}/__tests__/{filename}.test.ts`
   - Use path aliases for imports (`common/...`, `components/...`)

4. **Test structure requirements**
   - Use `describe` block for each exported function
   - Use `it.each` for table-driven tests when function has multiple input/output cases
   - Include edge cases: `null`, `undefined`, empty strings, empty arrays
   - Include boundary cases where applicable

5. **After generating, run the tests**
   ```bash
   npm run test:unit -- --testPathPatterns={filename}
   ```

## Test file pattern

```typescript
import { functionName } from 'common/path/to/file'

describe('functionName', () => {
  it.each`
    input        | expected
    ${value1}    | ${result1}
    ${value2}    | ${result2}
    ${null}      | ${expectedForNull}
    ${undefined} | ${expectedForUndefined}
  `('functionName($input) returns $expected', ({ input, expected }) => {
    expect(functionName(input)).toBe(expected)
  })
})
```

## Reference

See existing tests at:
- `common/utils/__tests__/format.test.ts`
- `common/utils/__tests__/featureFilterParams.test.ts`
