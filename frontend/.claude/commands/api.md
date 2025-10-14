---
description: Generate a new RTK Query API service using the SSG CLI
---

Use `npx ssg` to generate a new API service. Follow these steps:

1. Check backend code in `../api/` Django backend for endpoint details
   - Use `/backend <search>` to search for the endpoint
   - Look for URL patterns, views, and serializers
2. Run `npx ssg` and follow the interactive prompts
   - Choose operation type (get, create, update, delete, crud)
   - Enter the resource name (e.g., "Feature", "Environment")
3. Define request/response types in `common/types/requests.ts` and `responses.ts`
   - Add to the `Req` type for requests
   - Add to the `Res` type for responses
4. Verify the generated service URL matches the backend endpoint (usually `/api/v1/...`)
5. Use the generated hooks in components: `useGetXQuery()`, `useCreateXMutation()`

Context file: `.claude/context/api-integration.md`
