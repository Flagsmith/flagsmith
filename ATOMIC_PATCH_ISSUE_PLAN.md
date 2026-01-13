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

### Test 1: Unit Test (`tests/unit/segments/test_unit_segments_atomic.py`)

**Purpose**: Prove that during segment PATCH, identity evaluation can incorrectly return `True` for non-matching identities.

**Approach**:
1. Create project, environment, feature (default `enabled=False`)
2. Create segment with rule matching `flagEnabledId="enabled"`
3. Create feature segment override (`enabled=True`)
4. Create identity without matching trait (`disabled-identity`)
5. Monkeypatch `ConditionSerializer.create` to block mid-update (simulating slow DB)
6. In a separate thread, initiate segment PATCH
7. While blocked, call `identity.get_all_feature_states()`
8. **Expected (buggy)**: Identity receives `enabled=True` (incorrect)
9. **Expected (fixed)**: Identity receives `enabled=False` (correct)

```python
# Skeleton
@pytest.fixture
def segment_with_override(project, environment, feature):
    """Create segment matching flagEnabledId='enabled' with feature override."""
    segment = Segment.objects.create(name="Test Segment", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule,
        property="flagEnabledId",
        operator=EQUAL,
        value="enabled",
    )
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=True,
    )
    return segment

def test_segment_patch__mid_update__identity_does_not_incorrectly_match(
    segment_with_override,
    environment,
    feature,
    admin_client,
    mocker,
):
    # Given
    identity = Identity.objects.create(
        identifier="disabled-identity",
        environment=environment,
    )
    # No trait - identity should NOT match segment

    # Create blocking mechanism
    block_event = threading.Event()
    original_create = ConditionSerializer.create

    def blocking_create(self, validated_data):
        block_event.wait(timeout=5)  # Block until released
        return original_create(self, validated_data)

    mocker.patch.object(ConditionSerializer, 'create', blocking_create)

    # When - Start PATCH in background thread
    def do_patch():
        url = reverse("api-v1:projects:project-segments-detail",
                      args=[project.id, segment.id])
        admin_client.patch(url, data={...}, content_type="application/json")

    patch_thread = threading.Thread(target=do_patch)
    patch_thread.start()

    # Give PATCH time to start and delete old conditions
    time.sleep(0.1)

    # Then - Check flag state during PATCH window
    feature_states = identity.get_all_feature_states()
    flag = next(fs for fs in feature_states if fs.feature_id == feature.id)

    # Release block and clean up
    block_event.set()
    patch_thread.join()

    # Assert - Should NOT match segment (enabled=False)
    # Currently fails: enabled=True due to empty rule matching
    assert flag.enabled is False
```

### Test 2: Integration Test (`tests/integration/environments/identities/test_integration_segment_patch_atomic.py`)

**Purpose**: End-to-end test via API endpoints to prove the issue manifests in production-like conditions.

**Approach**:
1. Create segment, feature segment override, and identity using the core API
2. Run a 10s loop in a background thread that repeatedly PATCHes the same ruleset
3. In parallel, poll `api-v1:environments:identity-featurestates-all` for the identity
4. Capture any response where the feature is incorrectly enabled for the non-matching identity
5. Assert at least one mismatch was observed (fails once the fix is in place)

---

## Part 3: Fix Implementation

### Option A: Create-Before-Delete Strategy (Recommended)

**Rationale**: The safest fix is to ensure new rules/conditions exist before deleting old ones. This maintains segment integrity throughout the update.

**Implementation Steps**:

#### Step 1: Override `update` method in `SegmentSerializer`

Location: `api/segments/serializers.py`

```python
def update(self, segment: Segment, validated_data: dict[str, Any]):
    metadata = validated_data.pop("metadata", [])
    rules_data = validated_data.pop("rules", None)

    with transaction.atomic():
        # 1. Create revision if needed
        if not segment.change_request:
            segment_revision = segment.clone(is_revision=True)
            logger.info(
                "segment-revision-created",
                segment_id=segment.id,
                revision_id=segment_revision.id,
            )

        # 2. Update scalar fields only
        for attr, value in validated_data.items():
            setattr(segment, attr, value)
        segment.save()

        # 3. If rules provided, do atomic swap
        if rules_data is not None:
            self._atomic_update_rules(segment, rules_data)

    self._update_metadata(segment, metadata)
    return segment

def _atomic_update_rules(
    self,
    segment: Segment,
    rules_data: list[dict[str, Any]]
) -> None:
    """
    Atomically update segment rules by:
    1. Creating all new rules/conditions first
    2. Deleting old rules only after new ones exist

    This ensures the segment never has an empty rule tree.
    """
    # Get IDs of existing rules to delete later
    old_rule_ids = list(segment.rules.values_list('id', flat=True))

    # Create new rules (temporarily alongside old ones)
    new_rules = []
    for rule_data in rules_data:
        new_rule = self._create_rule_tree(segment, rule_data)
        new_rules.append(new_rule)

    # Now delete old rules (new ones already exist)
    SegmentRule.objects.filter(id__in=old_rule_ids).delete()

def _create_rule_tree(
    self,
    segment: Segment,
    rule_data: dict[str, Any],
    parent_rule: SegmentRule | None = None,
) -> SegmentRule:
    """Recursively create a rule with its conditions and nested rules."""
    conditions_data = rule_data.pop("conditions", [])
    nested_rules_data = rule_data.pop("rules", [])

    # Remove ID if present (we're creating new)
    rule_data.pop("id", None)
    rule_data.pop("delete", None)

    # Create the rule
    rule = SegmentRule.objects.create(
        segment=segment if parent_rule is None else None,
        rule=parent_rule,
        type=rule_data.get("type", SegmentRule.ALL_RULE),
    )

    # Create conditions
    for condition_data in conditions_data:
        condition_data.pop("id", None)
        condition_data.pop("delete", None)
        Condition.objects.create(rule=rule, **condition_data)

    # Recursively create nested rules
    for nested_rule_data in nested_rules_data:
        self._create_rule_tree(segment, nested_rule_data, parent_rule=rule)

    return rule
```

#### Step 2: Add database-level constraint (optional enhancement)

Consider adding a database trigger or constraint to prevent segments from having zero rules, as a safety net.

### Option B: SELECT FOR UPDATE Lock

**Alternative approach**: Use `select_for_update()` to lock the segment row during updates, preventing concurrent reads from seeing intermediate states.

```python
def update(self, segment: Segment, validated_data: dict[str, Any]):
    with transaction.atomic():
        # Lock the segment row
        segment = Segment.objects.select_for_update().get(pk=segment.pk)
        # ... rest of update
```

**Drawback**: This could cause contention and doesn't solve the fundamental issue of the empty rule window within the same transaction.

### Option C: Evaluator Guard (Defence in Depth)

**Supplementary fix**: Modify the flag engine evaluator to treat segments with empty rules as non-matching.

Location: `flag_engine/segments/evaluator.py` (in the flag-engine package)

```python
def is_context_in_segment(context: EvaluationContext, segment: SegmentModel) -> bool:
    rules = segment.rules
    if not rules:
        return False

    # Additional guard: check each rule has content
    for rule in rules:
        if not rule.conditions and not rule.rules:
            return False  # Empty rule = no match

    return all(
        context_matches_rule(context=context, rule=rule, segment_key=segment.id)
        for rule in rules
    )
```

**Note**: This requires changes to the `flagsmith-flag-engine` package.

---

## Part 4: Implementation Order

### Phase 1: Reproduction (Tests First)

1. **Create unit test file**: `tests/unit/segments/test_unit_segments_atomic.py`
   - Test that proves the bug exists
   - Mark with `@pytest.mark.xfail(reason="Atomic update not yet implemented")`

2. **Create integration test file**: `tests/integration/environments/identities/test_integration_segment_patch_atomic.py`
   - End-to-end test via API
   - Mark with `@pytest.mark.xfail`

3. **Commit**: `test: add failing tests for atomic segment PATCH issue`

### Phase 2: Fix Implementation

4. **Implement `_atomic_update_rules`** in `SegmentSerializer`
   - Create-before-delete strategy
   - Ensure all rule/condition creation happens before any deletion

5. **Update `update` method** to use new atomic approach

6. **Commit**: `fix(segments): make segment PATCH updates atomic`

### Phase 3: Test Verification

7. **Remove `xfail` markers** from tests
8. **Run full test suite** to ensure no regressions
9. **Commit**: `test: mark atomic segment tests as passing`

### Phase 4: Documentation & Cleanup

10. **Update ATOMIC_PATCH_ISSUE.md** with resolution notes
11. **Final commit**: `docs: document atomic segment PATCH fix`

---

## Part 5: Files to Modify

| File                                                                                 | Change Type | Description                                              |
| ------------------------------------------------------------------------------------ | ----------- | -------------------------------------------------------- |
| `api/segments/serializers.py`                                                        | Modify      | Override `update()` method, add `_atomic_update_rules()` |
| `tests/unit/segments/test_unit_segments_atomic.py`                                   | Create      | Unit test for atomic update                              |
| `tests/integration/environments/identities/test_integration_segment_patch_atomic.py` | Create      | Integration test                                         |
| `ATOMIC_PATCH_ISSUE.md`                                                              | Modify      | Update with resolution status                            |

---

## Part 6: Testing Requirements

### Database
- Tests require PostgreSQL (not SQLite) for proper transaction isolation
- Use `DATABASE_URL=postgres://postgres:password@localhost:55432/flagsmith`

### Markers
- Unit tests: `pytest tests/unit/segments/test_unit_segments_atomic.py`
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
