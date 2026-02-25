---
description: Find all usages of a component, function, or type
---

Find all usages of `$ARGUMENTS` across the frontend codebase.

## Steps

1. **Identify what we're searching for**
   - Component name (e.g., `Switch`, `Button`)
   - Function name (e.g., `isFreeEmailDomain`, `formatDate`)
   - Type/interface name (e.g., `FeatureState`, `ProjectFlag`)

2. **Find the definition**
   - Search for where it's defined/exported
   - Note the file path and export type (default vs named)

3. **Search for imports**
   ```bash
   # For named exports
   grep -r "import.*{ $SYMBOL" --include="*.ts" --include="*.tsx"

   # For default exports
   grep -r "import $SYMBOL" --include="*.ts" --include="*.tsx"
   ```

4. **Search for direct usages**
   - JSX usage: `<ComponentName`
   - Function calls: `functionName(`
   - Type annotations: `: TypeName` or `as TypeName`

5. **Categorise usages**
   - Group by file/directory
   - Note the context (component, hook, utility, test)

## Output format

```
## Definition
[File path where it's defined]

## Usages (X files)

### components/
- ComponentA.tsx:42 - Used in render
- ComponentB.tsx:15 - Passed as prop

### pages/
- FeaturePage.tsx:88 - Used in modal

### hooks/
- useFeature.ts:12 - Called in effect

## Impact Assessment
[Brief note on how widespread the usage is and what to consider when modifying]
```

## Use cases

- Before refactoring: understand what will be affected
- Before deleting: ensure nothing depends on it
- Before renaming: find all places that need updates
