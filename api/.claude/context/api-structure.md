# API Structure

## URL Patterns

### Features
- **Project Features**: `/api/v1/projects/{project_pk}/features/`
  - List/create features for a project
  - ViewSet: `FeatureViewSet`

- **Feature Detail**: `/api/v1/projects/{project_pk}/features/{id}/`
  - Retrieve/update/delete specific feature
  - ViewSet: `FeatureViewSet`

### Feature States

#### Environment Feature States
- **List/Create**: `/api/v1/environments/{api_key}/featurestates/`
  - Get feature states for environment (no segment/identity overrides)
  - ViewSet: `EnvironmentFeatureStateViewSet`
  - Filters: `feature`, `feature_name`, `anyIdentity` (deprecated)
  - New: `segment` parameter to filter segment overrides

- **Detail**: `/api/v1/environments/{api_key}/featurestates/{id}/`
  - Retrieve/update/delete specific feature state
  - ViewSet: `EnvironmentFeatureStateViewSet`

#### Identity Feature States
- **List/Create**: `/api/v1/environments/{api_key}/identities/{identity_pk}/featurestates/`
  - Feature states for specific identity
  - ViewSet: `IdentityFeatureStateViewSet`

- **All States**: `/api/v1/environments/{api_key}/identities/{identity_pk}/featurestates/all/`
  - Get all feature states for identity (including environment defaults)
  - ViewSet: `IdentityFeatureStateViewSet.all` action

#### Simple Feature States (Alternative Endpoint)
- **List/Create/Update**: `/api/v1/features/featurestates/`
  - Simpler endpoint for creating feature states
  - ViewSet: `SimpleFeatureStateViewSet`
  - Required param: `environment` (ID)

### Segments

#### Feature Segments (Segment Override Associations)
- **List/Create**: `/api/v1/features/feature-segments/`
  - Links segments to features with priority
  - ViewSet: `FeatureSegmentViewSet`
  - Required params: `environment` (ID), `feature` (ID)

- **Update Priorities**: `/api/v1/features/feature-segments/update-priorities/`
  - Batch update segment override priorities
  - ViewSet: `FeatureSegmentViewSet.update_priorities` action

#### Segments
- **List/Create**: `/api/v1/projects/{project_pk}/segments/`
  - Manage segments for a project

### Segment Overrides (Legacy Endpoint)
- **Create**: `/api/v1/environments/{api_key}/features/{feature_pk}/create-segment-override/`
  - Create segment override for a feature
  - Function: `create_segment_override`

## Key ViewSets

### FeatureViewSet
- **Location**: `api/features/views.py`
- **Purpose**: Manage features at project level
- **Permissions**: `FeaturePermissions`
- **Filters**: `environment`, `search`, `tags`, `is_archived`, `owners`, `group_owners`, `value_search`, `is_enabled`

### EnvironmentFeatureStateViewSet
- **Location**: `api/features/views.py`
- **Base Class**: `BaseFeatureStateViewSet`
- **Purpose**: Manage environment-level feature states (base states + segment overrides)
- **Permissions**: `EnvironmentFeatureStatePermissions`
- **Default Filter**: `feature_segment=None, identity=None` (base states only)
- **New**: Can filter by `segment` parameter to get segment overrides

### IdentityFeatureStateViewSet
- **Location**: `api/features/views.py`
- **Base Class**: `BaseFeatureStateViewSet`
- **Purpose**: Manage identity-specific feature state overrides
- **Permissions**: `IdentityFeatureStatePermissions`
- **Filter**: `identity__pk={identity_pk}`

### FeatureSegmentViewSet
- **Location**: `api/features/feature_segments/views.py`
- **Purpose**: Manage feature-segment associations (which segments override which features)
- **Permissions**: `FeatureSegmentPermissions`
- **Required Filters**: `environment` (ID), `feature` (ID)

## Feature Versioning

### v1 (Default)
- Feature states directly on environment
- No versioning or scheduling
- Filter: `environment=<env>`

### v2 (Optional)
- Feature states via `EnvironmentFeatureVersion`
- Supports versioning and scheduling of changes
- Enabled per environment: `environment.use_v2_feature_versioning = True`
- Uses `get_current_live_environment_feature_version()` to get active version
- Filter: `environment_feature_version=<version>`

### Checking Version in Views
```python
if environment.use_v2_feature_versioning:
    queryset = queryset.filter(
        environment_feature_version=get_current_live_environment_feature_version(
            environment_id=environment_id,
            feature_id=feature_id,
        )
    )
```

## Common Query Patterns

### Get Environment Feature States (Base States Only)
```python
GET /api/v1/environments/{api_key}/featurestates/
# Returns: Feature states where feature_segment=None and identity=None
```

### Get Segment Override States
```python
GET /api/v1/environments/{api_key}/featurestates/?segment={segment_id}
# Returns: Feature states where feature_segment.segment_id={segment_id}
```

### Get Feature State by Feature
```python
GET /api/v1/environments/{api_key}/featurestates/?feature={feature_id}
# Returns: Feature states for specific feature
```

### Get All Identity States
```python
GET /api/v1/environments/{api_key}/identities/{identity_pk}/featurestates/all/
# Returns: All feature states with identity overrides + environment defaults
```

## Authentication

### User Authentication
- Django session auth
- Token auth
- Required for dashboard/admin endpoints

### Environment Key Authentication
- Header: `X-Environment-Key: {api_key}`
- Used for SDK endpoints
- Limited to environment-specific operations

### Master API Key Authentication
- Full access to organization
- Used for automation/integrations
