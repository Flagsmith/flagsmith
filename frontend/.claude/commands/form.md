---
description: Create a new form using Yup + Formik pattern
---

Create a form following the standard pattern:

1. Use `useFormik` hook with `validationSchema` from Yup
2. Always include `validateOnMount: true`
3. Use `validateForm` utility from `project/utils/forms/validateForm` in submit handler
4. Use `InputGroup` component with `touched` and `error` props
5. For special inputs (date, phone, select), use `component` prop on InputGroup

Reference: `/examples/forms/ComprehensiveFormExample.tsx`

Context file: `.claude/context/forms.md`
