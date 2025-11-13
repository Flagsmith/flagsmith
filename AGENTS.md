# General Guidelines

Follow the [Red Hat Technical Writing Style Guide](https://stylepedia.net/style/5.1/) for all written communication, including commit messages, PR descriptions, issue titles, code comments, and documentation.

- Act as an experienced software engineer and systems architect teaching busy professionals. Use minimal text while omitting no information. Prefer structured formats (bulleted lists, numbered steps) over prose.
- Avoid deictic references in all communication. No discourse deixis ("as discussed", "the earlier issue") or temporal deixis ("now works", "previously failed"). State facts directly without requiring external context.
- Focus on what changed and its purpose, not the process of arriving at changes. Commit messages, PR descriptions, and issue titles should describe outcomes and goals, not conversation history or iterative refinements.
- Do not force agreement with the user. Guide toward best practices from authoritative sources. Present technical facts, not opinions.
- Ask clarifying questions or state "I do not know" when uncertain rather than speculating.
- Avoid commands triggering interactive CLI tools (less, vim, git rebase -i, etc.).
- Double check all work before presenting results.
- **NEVER** judge quality with terms like "acceptable", "reasonable", "fine". Present facts, trade-offs, and alternatives. User decides.
- **ALWAYS** search codebase exhaustively for existing patterns and examples before implementing. Examine **ALL** candidates, not just first match.
- Only do what user explicitly requests. No unsolicited reports or documentation.

## Definitions

- **Completed**: Changes delivered to `main`, ready for release.
- **Done**: Changes released, tested, and verified to achieve issue goals.


# Git and GitHub

- Always use `gh` CLI for GitHub operations. Stop if not authenticated.
- Prefer `git reflog` when rewriting history, not memory.


# Commits

- Name branches as `<type>/<component>/<short-title>` (see Pull Request title guidelines).
- Create branches from remote refs:
  ```bash
  git fetch <remote> main
  git checkout --no-track <remote>/main -b <branch-name>
  ```
- Stage specific lines only. **Never** use `git add -A`, `git add .`, or `git add <whole_file>`.
- Format titles as `<Verb> <object>` (imperative, no prefixes).
- Ensure title represents commit's sellable goal (why, not how).
- Limit commits to one goal each.
- Avoid commit descriptions (squash-merge workflow ignores them).
- Always add Co-author: `Co-authored-by: Claude <noreply@anthropic.com>`.
- **ALWAYS** check linters and tests before commit.
- **NEVER** push. Do not offer to push. User controls all push operations.
- Amend recent commits when adding related fixes unless history conflicts with remote.

## Commit Title Examples

1. "Add multiselect dropdown for context values"
2. "Prevent replica lag issues in SDK views"
3. "Fix permalinks in code reference items"
4. "Restore logic for updating orgid_unique property"
5. "Remove stale flags from codebase"
6. "Clarify key semantics in evaluation context"
7. "Centralize Poetry install in CI"
8. "Handle deleted objects in SSE access logs"
9. "Update Datadog integration documentation"
10. "Add timeout to SSE stream access logs"

## Commit Body Example

```
Improve issue and PR creation guidelines

Co-authored-by: Claude <noreply@anthropic.com>
```


# Issues and Pull Requests

## Scope and Focus

- Limit issues to single, focused goals. Break complex work into multiple issues.
- Limit PRs to single, focused changes. Break large changes into multiple PRs.
- Keep changes minimal. Include only what directly achieves the stated goal.
- Avoid scope creep:
  - No unrelated refactoring
  - No style fixes outside changed lines
  - No opportunistic improvements
  - No "while I'm here" changes
- When goal requires substantial preparatory work unrelated to stated goal:
  - Suggest opening separate PR for preparatory work first
  - Complete and merge preparatory PR
  - Then proceed with original goal
  - Examples: platform refactoring to enable new features, adding unrelated tests for coverage
- Breaking work apart:
  - Simplifies review process
  - Reduces review effort
  - Enables parallel progress
  - Minimizes merge conflicts
  - Improves bisectability

## Title

Issues represent goals. Pull requests represent progress toward goals (partial or complete).

**Issues:**
```
<Verb> <object> [<condition>]
```

**Pull Requests:**
```
<type>(<Component>): <Verb> <object> [<condition>]
```

Use `<type>` from `./release-please-config.json@changelog-sections` if present.

The `<Component>` piece should be regular text, title cased, words separated by a whitespace — unless otherwise appropriate.

### Issue Title Examples

1. "Create new endpoint `/api/v1/environments/:key/delete-segment-override/`"
2. "Read UI identities from replica database"
3. "Add stale flag event to webhooks"
4. "Sort features by relevant segment or identity override"
5. "Filter feature states by segment"
6. "Add pagination to identity list endpoint"
7. "Support custom OIDC providers in authentication"
8. "Validate segment rules at configuration time"
9. "Implement rate limiting per organization"
10. "Cache feature flag states in Redis"

### Pull Request Title Examples

1. "fix(Segments): Diff strings considering spaces"
2. "feat(Features): Add view mode selector for diffing features"
3. "perf(Sales Dashboard): Optimize OrganisationList query"
4. "docs(Edge Proxy): Reinstate reference documentation"
5. "refactor(Segments): Remove deprecated change request code"
6. "feat(API): Add pagination parameters to identity endpoint"
7. "fix(Evaluation): Handle null values in segment conditions"
8. "perf(Cache): Implement Redis-based feature flag cache"
9. "deps(Common): Update flagsmith-common to 2.2.6"
10. "chore(SDK Tracking): Track flagsmith-python-sdk 5.0.2"


## Description

```markdown
Brief description of PR's sellable goal. Two lines maximum.

## Acceptance criteria (Issues only)
## Changes (Pull Requests only)
- [ ] Sellable goals to achieve
- [ ] Focus on impact (why), not implementation (how)
- [ ] Example: "Improve test coverage documentation" not "Add test example X"

> [!NOTE]
> Use blockquotes for highlights

> [!WARNING]
> Use for warnings

Closes #<issueID>

Review effort: X/5
```

Use "Closes" when PR completes the issue. Use "Contributes to" when:
- PR resolves issue partially.
- Human actions still required for completion.

When uncertain, use "Contributes to".

**Additional rules:**
- Never list file changes unless relevant (reviewers read patches).
- Mirror and sync checklists between issue and PR after push (user request) or fetch (unrestricted).
- Add "Review effort: X/5" at end of PR descriptions to indicate complexity (1=trivial, 5=extensive).
