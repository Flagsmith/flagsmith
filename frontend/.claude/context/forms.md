# Form Patterns (Custom Components)

**IMPORTANT**: This codebase does NOT use Formik or Yup. Forms are built with custom form components.

## Standard Pattern for Forms

```typescript
import { FC, FormEvent, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

type FormData = {
  name: string
  email: string
}

const MyForm: FC = () => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
  })
  const [error, setError] = useState<any>(null)

  const setFieldValue = (key: keyof FormData, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }

  const isValid = !!formData.name && Utils.isValidEmail(formData.email)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (isValid) {
      // Make API call
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <InputGroup
        title='Name'
        isValid={!!formData.name && !error?.name}
        inputProps={{
          error: error?.name,
          name: 'name',
        }}
        value={formData.name}
        onChange={(e: FormEvent) => setFieldValue('name', e)}
      />
      <InputGroup
        title='Email'
        type='email'
        isValid={Utils.isValidEmail(formData.email) && !error?.email}
        inputProps={{
          error: error?.email,
          name: 'email',
        }}
        value={formData.email}
        onChange={(e: FormEvent) => setFieldValue('email', e)}
      />
      <Button type="submit" disabled={!isValid}>Submit</Button>
    </form>
  )
}
```

## Form Components (in `web/components/base/forms/`)

- **InputGroup**: Main form field wrapper
  - Props: `title`, `value`, `onChange`, `isValid`, `inputProps`, `type`
  - `inputProps` can contain `error`, `name`, `className`, etc.
- **Button**: Standard button component
- **Select**: Dropdown select component
- **Switch**, **Toggle**: Boolean inputs

## Validation Patterns

- **Custom validation**: Use inline checks with `Utils` helpers
  - `Utils.isValidEmail(email)`
  - Custom business logic
- **isValid prop**: Controls visual feedback (green checkmark, etc.)
- **Error handling**: Pass `error` via `inputProps` for field-level errors

## Example with RTK Query Mutation

```typescript
const [createEntity, { isLoading, error: apiError }] = useCreateEntityMutation()

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault()
  if (!isValid) return

  try {
    await createEntity(formData).unwrap()
    // Success - show toast, redirect, etc.
  } catch (err) {
    // Handle error
    setError(err)
  }
}
```

**Reference**: See actual forms in `web/components/onboarding/` for real examples
