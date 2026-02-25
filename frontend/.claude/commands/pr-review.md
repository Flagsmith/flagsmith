---
description: Review a GitHub pull request
---

Review the pull request at `$ARGUMENTS`.

## Steps

1. **Fetch PR details**
   ```bash
   gh pr view <PR_NUMBER_OR_URL> --json title,body,files,additions,deletions,state,headRefName
   ```

2. **Get the diff**
   ```bash
   gh pr diff <PR_NUMBER_OR_URL>
   ```

3. **Analyse the changes**
   - Summarise what the PR does
   - Check if the approach makes sense
   - Identify potential issues:
     - Missing edge cases
     - Inconsistencies with existing patterns
     - Code style issues (indentation, naming)
     - Missing tests for new functionality
   - Check if related files need updates

4. **Review against project patterns**
   - Does it follow patterns in `.claude/context/`?
   - Are imports using path aliases (`common/`, `components/`)?
   - Is state management using RTK Query where appropriate?

5. **Provide feedback**
   - Summary of what the PR does
   - What's good about the approach
   - Potential concerns or suggestions
   - Questions for the author (if any)

## Output format

```
## PR Summary
[Brief description of what the PR does]

## Changes
[List of files changed and what each change does]

## Assessment
✅ What looks good
⚠️ Potential concerns
💡 Suggestions

## Questions
[Any clarifying questions for the author]
```
