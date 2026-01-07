# Form Patterns (Yup + Formik)

## Standard Pattern for ALL Forms

```typescript
import { useFormik } from 'formik'
import * as yup from 'yup'
import { validateForm } from 'project/utils/forms/validateForm'

const schema = yup.object().shape({
  name: yup.string().required('Name is required'),
})

const MyForm = () => {
  const { errors, touched, values, handleChange, handleBlur, handleSubmit, setTouched } = useFormik({
    initialValues: { name: '' },
    onSubmit: async (values) => { /* API call */ },
    validationSchema: schema,
    validateOnMount: true,
  })

  const onSubmit = async (e) => {
    e.preventDefault()
    const isValid = await validateForm(errors, setTouched)
    if (isValid) handleSubmit()
  }

  return (
    <form onSubmit={onSubmit}>
      <InputGroup
        name="name"
        value={values.name}
        onChange={handleChange}
        onBlur={handleBlur}
        touched={touched.name}
        error={errors.name}
      />
      <Button type="submit">Submit</Button>
    </form>
  )
}
```

## Form Components (in `components/base/forms/`)

- **InputGroup**: Standard wrapper - pass `touched` and `error` props
- **DatePicker**, **PhoneInput**, **Select**: Use with `component` prop on InputGroup
- **Radio**, **Checkbox**, **Switch**: Boolean/choice inputs

**Reference**: See `/examples/forms/ComprehensiveFormExample.tsx`

## Form Spacing & Layout

### Standard Form Layout Structure

```tsx
<div className='card shadow-sm h-100'>
  <div className='card-body p-4'>
    <h2 className='h4 mb-4 pb-3 border-bottom'>Form Title</h2>

    <div className='d-flex flex-column gap-4'>
      <InputGroup name='field1' ... />
      <InputGroup name='field2' ... />
      <InputGroup name='field3' ... />
    </div>
  </div>
</div>
```

### Spacing Classes

Use Bootstrap's spacing scale consistently:

- **Between InputGroups**: `d-flex flex-column gap-4` (24px vertical gap)
- **Section header margin**: `h3 className='mb-4 pb-3 border-bottom'` (24px bottom)
- **Two-column rows**: `d-flex gap-4 mb-4` with `flex-1` per column
- **Button rows**: `d-flex justify-content-end gap-2 mt-3` (8px between buttons, 16px top margin)
- **Error messages**: `mb-5` when standalone (48px)

### Multi-Section Forms

For forms with multiple sections:

```tsx
<form onSubmit={onSubmit}>
  <div className='d-flex flex-column gap-5'> {/* 48px between sections */}

    {/* Section 1 */}
    <div>
      <h3 className='mb-4'>Section Title</h3>
      <div className='d-flex flex-column gap-4'>
        <InputGroup ... />
        <InputGroup ... />
      </div>
    </div>

    {/* Section 2 */}
    <div>
      <h3 className='mb-4'>Another Section</h3>
      <div className='d-flex flex-column gap-4'>
        <InputGroup ... />
      </div>
    </div>

    {/* Actions */}
    <div className='d-flex justify-content-end gap-2 mt-3'>
      <Button>Cancel</Button>
      <Button type='submit'>Submit</Button>
    </div>
  </div>
</form>
```

### Bootstrap Gap/Margin Scale

- `gap-2` = 0.5rem (8px)
- `gap-3` = 1rem (16px)
- `gap-4` = 1.5rem (24px) ← Use for InputGroup spacing
- `gap-5` = 3rem (48px) ← Use for section separation

- `mb-3` = 1rem (16px)
- `mb-4` = 1.5rem (24px) ← Use for section headers
- `mb-5` = 3rem (48px) ← Use for standalone errors/content

### Key Files with Examples

- `/components/examples/forms/ComprehensiveFormExample.tsx` - Full pattern with sections
- `/components/ChangeAccountInformation.tsx` - Account form spacing
- `/components/ChangeContact.tsx` - Contact form spacing
- `/components/whatsapp/CreateEditNumber.tsx` - Modal form pattern
