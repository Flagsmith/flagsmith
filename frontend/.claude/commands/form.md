---
description: Create a new form component
---

**Note**: This codebase does NOT use Formik or Yup.

Create a form following the standard pattern:

1. Use React class component or functional component with `useState`
2. Use `InputGroup` component from global scope with `title`, `value`, `onChange`
3. For RTK Query mutations, use `useCreateXMutation()` hooks
4. Handle loading and error states
5. Use `Utils.preventDefault(e)` in submit handler
6. Use `toast()` for success/error messages
7. Use `closeModal()` to dismiss modal forms

Examples to reference:
- `web/components/SamlForm.js` - Class component form
- `web/components/modals/CreateSegmentRulesTabForm.tsx` - Functional component form
- Search for `InputGroup` usage in `/web/components/` for more examples

Context file: `.claude/context/forms.md`
