# Testing Guide

## Test Organization

### Directory Structure
- **Unit tests**: `api/tests/unit/` - Mock dependencies, test logic in isolation
- **Integration tests**: `api/tests/integration/` - Real DB, test full flow with dependencies
- View tests typically go in: `tests/unit/<app>/test_unit_<app>_views.py`
- Model tests: `tests/unit/<app>/test_unit_<app>_models.py`
- Serializer tests: `tests/unit/<app>/test_unit_<app>_serializers.py`

### When to Use Each Type
- **Unit tests**: Testing view logic, permissions, query filtering, serialization
- **Integration tests**: Testing full request/response cycle, DB transactions, complex workflows

## Running Tests

### Commands (from api/ directory)

```bash
# Run all tests
make test

# Run a single test file
make test opts="path/to/test_file.py"

# Run a single test case
make test opts="path/to/test_file.py::test_function_name"

# Run tests matching a pattern
make test opts="-k test_pattern"

# Run with verbose output
make test opts="-v"

# Run with print statements visible
make test opts="-s"
```

### Examples

```bash
# Run all feature view tests
make test opts="tests/unit/features/test_unit_features_views.py"

# Run a specific test
make test opts="tests/unit/features/test_unit_features_views.py::test_list_feature_states_for_segment"

# Run all segment-related tests
make test opts="-k segment"
```

## Common Testing Patterns

### URL Reversal
```python
from django.urls import reverse

# Environment feature states list
url = reverse(
    "api-v1:environments:environment-featurestates-list",
    args=[environment_api_key]
)

# With detail
url = reverse(
    "api-v1:environments:environment-featurestates-detail",
    args=[environment_api_key, feature_state_id]
)
```

### Parametrized Tests
```python
import pytest
from pytest_lazyfixture import lazy_fixture

@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_something(client, environment):
    # Test with both regular admin and master API key
    response = client.get(url)
    assert response.status_code == 200
```

### Using Fixtures
Common fixtures available in conftest.py:
- `admin_client` - Authenticated admin user client
- `admin_master_api_key_client` - Master API key authenticated client
- `environment` - Test environment
- `project` - Test project
- `organisation` - Test organisation
- `feature` - Test feature
- `segment` - Test segment

## Important Testing Rules

### Mock External Calls
Always mock external API calls, network requests, and third-party services:

```python
from unittest.mock import patch

@patch('requests.post')
def test_webhook_call(mock_post, environment):
    mock_post.return_value.status_code = 200
    # Test code that triggers webhook
```

### Versioning Tests
Test both v1 (default) and v2 feature versioning paths when relevant:

```python
def test_with_v1_versioning(environment, feature):
    # v1 is default
    assert environment.use_v2_feature_versioning is False
    # test v1 behavior

def test_with_v2_versioning(environment, feature):
    environment.use_v2_feature_versioning = True
    environment.save()
    # test v2 behavior with EnvironmentFeatureVersion
```

### Permission Tests
Test permission boundaries:

```python
from common.environments.permissions import UPDATE_FEATURE_STATE, VIEW_ENVIRONMENT

def test_user_without_permission_cannot_update(
    organisation_one_user,
    organisation_one_project_one_environment_one,
):
    client = get_environment_user_client(
        user=organisation_one_user,
        environment=organisation_one_project_one_environment_one,
        permission_keys=[VIEW_ENVIRONMENT],  # No UPDATE_FEATURE_STATE
    )

    response = client.patch(url, data=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
```

## Test Data Patterns

### Creating Test Data
```python
from features.models import Feature, FeatureState, FeatureSegment
from segments.models import Segment

# Create a segment override
segment = Segment.objects.create(name="test_segment", project=project)
feature_segment = FeatureSegment.objects.create(
    feature=feature,
    segment=segment,
    environment=environment,
    priority=0,
)
segment_feature_state = FeatureState.objects.create(
    feature=feature,
    environment=environment,
    feature_segment=feature_segment,
    enabled=True,
)
```

### Asserting Response Data
```python
response = client.get(url)
assert response.status_code == status.HTTP_200_OK

response_json = response.json()
assert response_json["count"] == 2
assert len(response_json["results"]) == 2
assert response_json["results"][0]["feature"] == feature.id
```

## Debugging Tests

### Running with pdb
```bash
make test opts="-s --pdb path/to/test.py::test_name"
```

### Print Debugging
```bash
make test opts="-s path/to/test.py::test_name"
```

### Checking Test Coverage
```bash
make test opts="--cov=features --cov-report=html tests/unit/features/"
```
