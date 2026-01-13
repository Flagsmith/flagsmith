@@ -0,0 +1,400 @@
# Atomic Segment PATCH Issue - Implementation Plan

## Executive Summary

This document outlines the plan to reproduce and fix the atomic segment PATCH issue where segment updates can temporarily expose an empty rule tree, causing incorrect flag evaluation for non-matching identities.

---

## Part 1: Root Cause Analysis

### Current Implementation Flow

The segment PATCH update follows this flow:

1. **Request arrives** at `SegmentViewSet.partial_update()` (inherited from DRF `ModelViewSet`)
2. **Serializer initialisation** in `SegmentSerializer.__init__()` filters out rules/conditions marked with `delete: true`
3. **Update method** in `SegmentSerializer.update()` (`api/segments/serializers.py:132-144`):
   - Wraps in `transaction.atomic()`
   - Creates a segment revision (clone)
   - Calls `super().update()` → `WritableNestedModelSerializer.update()`
4. **WritableNestedModelSerializer** (from `drf_writable_nested` library):
   - Calls `update_or_create_reverse_relations()` to process nested rules/conditions
   - Calls `delete_reverse_relations_if_need()` to delete objects not in new data

### The Problem

The `WritableNestedModelSerializer` from `drf_writable_nested` library processes updates in this order:

1. **Delete** old nested objects not present in the new data
2. **Create/Update** new nested objects

This creates a window where:
- Old rules/conditions are deleted
- New rules/conditions haven't been created yet
- The segment has an empty or incomplete rule tree

### Flag Engine Behaviour

In `flag_engine/segments/evaluator.py`:

```python
def context_matches_rule(context, rule, segment_key):
    matches_conditions = (
        rule.matching_function([...])
        if (conditions := rule.conditions)
        else True  # <-- Empty conditions = True!
    )
```

**Critical**: A rule with empty conditions evaluates to `True`, causing any identity to match the segment during the PATCH window.

---

## Part 2: Reproduction Strategy

### Integration Test (`tests/integration/environments/identities/test_integration_segment_patch_atomic.py`)

**Purpose**: End-to-end test via API endpoints to prove the issue manifests in production-like conditions.

**Approach**:
1. Create segment, feature segment override, and identity using the core API
2. Start a background thread that repeatedly PATCHes the same ruleset for ~10 seconds
3. In parallel, poll `api-v1:environments:identity-featurestates-all` for the identity
4. Capture any response where the feature is incorrectly enabled for the non-matching identity
5. Assert no mismatches were observed (current behaviour should surface a mismatch and fail)

**Notes**:
- No monkeypatching or synthetic delays; rely on real API behaviour and looped sampling
- Core API first; edge API reproduction can follow once core is captured

---

## Part 3: Fix Implementation

**Principles**:
- Avoid windows where a segment has an empty or incomplete rule tree
- Keep segment reads consistent during PATCH requests
- Validate any fix against the failing integration test before iterating further

---

## Part 4: Implementation Order

### Phase 1: Reproduction (Tests First)

1. **Create integration test file**: `tests/integration/environments/identities/test_integration_segment_patch_atomic.py`
   - End-to-end test via API
   - Must fail against current behaviour
2. **Commit**: `test: add failing integration repro for segment patch race`

### Phase 2: Fix Implementation

3. **Implement fix** guided by the failing integration test
4. **Commit**: `fix(segments): eliminate segment patch race`

### Phase 3: Verification

5. **Run integration test** to confirm it passes
6. **Commit** if further adjustments are required

### Phase 4: Documentation & Cleanup

7. **Update ATOMIC_PATCH_ISSUE.md** with resolution notes
8. **Final commit**: `docs: document atomic segment PATCH fix`

---

## Part 5: Files to Modify

| File                                                                                 | Change Type | Description                                              |
| ------------------------------------------------------------------------------------ | ----------- | -------------------------------------------------------- |
| `tests/integration/environments/identities/test_integration_segment_patch_atomic.py` | Create      | Integration reproduction test                            |
| `api/segments/serializers.py`                                                        | Modify      | Fix implementation (TBD)                                 |
| `ATOMIC_PATCH_ISSUE.md`                                                              | Modify      | Update with resolution status                            |

---

## Part 6: Testing Requirements

### Database
- Tests require PostgreSQL (not SQLite) for proper transaction isolation
- Use `DATABASE_URL=postgres://postgres:password@localhost:55432/flagsmith`

### Markers
- Integration tests: `pytest tests/integration/environments/identities/test_integration_segment_patch_atomic.py`

### Coverage
- Ensure 100% coverage on new code paths
- Test edge cases:
  - Empty rules list in PATCH
  - Nested rules (3+ levels)
  - Concurrent PATCH requests
  - PATCH during identity evaluation

---

## Part 7: Risks and Mitigations

| Risk                                             | Mitigation                                        |
| ------------------------------------------------ | ------------------------------------------------- |
| Performance regression from create-before-delete | Measure baseline, ensure < 10% increase           |
| Breaking existing API contracts                  | Ensure response format unchanged                  |
| Race conditions in concurrent updates            | Transaction isolation handles this                |
| Memory usage from holding old + new rules        | Rules are small; temporary duplication acceptable |

---

## Part 8: Success Criteria

1. **Bug reproduction tests pass** (after fix)
2. **No regression in existing segment tests**
3. **Identity evaluation returns correct flag value during PATCH**
4. **Performance impact < 10% on segment PATCH operations**
5. **Full test coverage (100%) on new code**

---

## Appendix: Key Code Locations

| Component                         | File                                    | Lines    |
| --------------------------------- | --------------------------------------- | -------- |
| SegmentSerializer                 | `api/segments/serializers.py`           | 81-202   |
| SegmentSerializer.update()        | `api/segments/serializers.py`           | 132-144  |
| SegmentViewSet                    | `api/segments/views.py`                 | 41-149   |
| Identity.get_segments()           | `api/environments/identities/models.py` | 143-187  |
| Identity.get_all_feature_states() | `api/environments/identities/models.py` | 58-132   |
| WritableNestedModelSerializer     | `drf_writable_nested` package           | External |
| Flag engine evaluator             | `flag_engine/segments/evaluator.py`     | External |
| identity_matching_segment fixture | `api/conftest.py`                       | 535-546  |
