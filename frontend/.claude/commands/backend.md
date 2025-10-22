---
description: Search the backend codebase for endpoint details
---

Search the `../api/` Django backend codebase for the requested endpoint.

Look for:
1. **URLs**: `../api/<app>/urls.py` - Route definitions and URL patterns
2. **Views**: `../api/<app>/views.py` - ViewSets and API logic
3. **Serializers**: `../api/<app>/serializers.py` - Request/response schemas
4. **Models**: `../api/<app>/models.py` - Data models
5. **Permissions**: Check for permission classes and authentication requirements

Common Django apps in Flagsmith:
- `organisations/` - Organization management
- `projects/` - Project management
- `environments/` - Environment configuration
- `features/` - Feature flags
- `segments/` - User segments
- `users/` - User management
- `audit/` - Audit logging

API base URL: `/api/v1/`
