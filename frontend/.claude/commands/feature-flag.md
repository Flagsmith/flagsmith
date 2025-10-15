---
description: Create a new feature flag UI component or integration
---

**Note**: This codebase IS Flagsmith - the feature flag platform itself.

When working with feature flag components:

1. **Understand the data model**:
   - Features belong to Projects
   - Feature States are per Environment (enabled/disabled, value)
   - Segment Overrides target specific user groups
   - Identity Overrides are for specific users

2. **Check existing components**:
   - Search for similar components: `find web/components -name "*Feature*"`
   - Look at Environment management patterns
   - Review Segment override implementations

3. **API patterns**:
   - Features: `/api/v1/projects/{id}/features/`
   - Feature States: `/api/v1/environments/{id}/featurestates/`
   - Check existing services in `common/services/useFeature*.ts`

4. **Common operations**:
   - Toggle feature on/off in environment
   - Update feature state value
   - Add segment overrides
   - Add identity overrides
   - View audit history

Context file: `.claude/context/feature-flags.md`
