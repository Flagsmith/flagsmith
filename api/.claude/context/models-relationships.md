# Key Model Relationships

## Core Models

### Feature (`features/models.py`)
- `project`: FK to Project
- `name`: Feature name (unique per project)
- `type`: STANDARD, MULTIVARIATE
- `default_enabled`: Default enabled state
- `is_server_key_only`: Hide from client-side SDKs

### FeatureState (`features/models.py`)
The value/enabled state of a feature in a specific context.

**Key Fields**:
- `feature`: FK to Feature (required)
- `environment`: FK to Environment (required)
- `identity`: FK to Identity (nullable - for identity overrides)
- `feature_segment`: FK to FeatureSegment (nullable - for segment overrides)
- `feature_state_value`: OneToOne to FeatureStateValue
- `enabled`: Boolean enabled state
- `environment_feature_version`: FK to EnvironmentFeatureVersion (nullable - v2 only)

**Three Types**:
1. **Base State**: `identity=None`, `feature_segment=None`
2. **Segment Override**: `feature_segment=<FeatureSegment>`, `identity=None`
3. **Identity Override**: `identity=<Identity>`, `feature_segment=None`

### FeatureStateValue (`features/models.py`)
Stores the actual value (string, int, or boolean).
- `feature_state`: OneToOne to FeatureState
- `type`: STRING, INTEGER, BOOLEAN
- `string_value`, `integer_value`, `boolean_value`

### FeatureSegment (`features/feature_segments/models.py`)
Links Feature + Segment + Environment with priority.

- `feature`: FK to Feature
- `segment`: FK to Segment
- `environment`: FK to Environment
- `priority`: Integer (0 = highest priority)
- `environment_feature_version`: FK to EnvironmentFeatureVersion (nullable - v2 only)

**Important**: The override values are in FeatureState with `feature_segment=<this FeatureSegment>`

### Segment (`segments/models.py`)
- `project`: FK to Project
- `name`: Segment name
- `rules`: JSON field with segment rules

### Environment (`environments/models.py`)
- `project`: FK to Project
- `api_key`: Unique API key for SDK access
- `use_v2_feature_versioning`: Boolean (enables v2 versioning)

## Segment Override Structure

```
FeatureSegment (links Feature + Segment + Environment)
    └─> FeatureState (the actual override)
        ├─> feature_segment = <FeatureSegment>
        ├─> identity = None
        └─> FeatureStateValue (actual value)
```

## Common Query Patterns

### Base Environment Feature States
```python
FeatureState.objects.filter(
    environment=environment,
    feature_segment=None,
    identity=None
)
```

### Segment Override Feature States
```python
FeatureState.objects.filter(
    environment=environment,
    feature_segment__segment=segment,
    identity=None
)
```

### Identity Override Feature States
```python
FeatureState.objects.filter(
    environment=environment,
    identity=identity
)
```

## Versioning (v2)

### EnvironmentFeatureVersion (`features/versioning/models.py`)
Version container for feature states (enables scheduling/versioning).
- `environment`: FK to Environment
- `feature`: FK to Feature
- `published_at`: DateTime (when version went live)

### Querying with v2
```python
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version
)

if environment.use_v2_feature_versioning:
    version = get_current_live_environment_feature_version(
        environment_id=environment.id,
        feature_id=feature.id
    )
    feature_states = FeatureState.objects.filter(
        environment_feature_version=version
    )
else:
    feature_states = FeatureState.objects.filter(
        environment=environment,
        environment_feature_version=None
    )
```

## Useful Select Related

```python
# Feature State with full context
FeatureState.objects.select_related(
    'feature',
    'environment',
    'feature_state_value',
    'identity',
    'feature_segment__segment'
)
```
