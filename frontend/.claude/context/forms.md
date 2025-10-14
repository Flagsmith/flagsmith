# Form Patterns

## Standard Pattern for ALL Forms

**NOTE**: This codebase does NOT use Formik or Yup. Use custom form components from global scope.

```javascript
import React, { Component } from 'react'

class MyForm extends Component {
  constructor() {
    super()
    this.state = {
      name: '',
      isLoading: false,
      error: null,
    }
  }

  handleSubmit = (e) => {
    Utils.preventDefault(e)
    if (this.state.isLoading) return

    // Basic validation
    if (!this.state.name) {
      this.setState({ error: 'Name is required' })
      return
    }

    this.setState({ isLoading: true, error: null })

    // Make API call
    data.post(`${Project.api}endpoint/`, { name: this.state.name })
      .then(() => {
        toast('Success!')
        closeModal()
      })
      .catch((error) => {
        this.setState({ error: error.message, isLoading: false })
      })
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <InputGroup
          inputProps={{ className: 'full-width' }}
          title="Name"
          value={this.state.name}
          onChange={(e) => this.setState({ name: Utils.safeParseEventValue(e) })}
        />
        {this.state.error && <ErrorMessage error={this.state.error} />}
        <Button type="submit" disabled={this.state.isLoading}>
          Submit
        </Button>
      </form>
    )
  }
}
```

## Functional Component Pattern (Modern)

```javascript
import { FC, useState } from 'react'

const MyForm: FC = () => {
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    Utils.preventDefault(e)
    if (isLoading) return

    if (!name) {
      setError('Name is required')
      return
    }

    setIsLoading(true)
    setError(null)

    data.post(`${Project.api}endpoint/`, { name })
      .then(() => {
        toast('Success!')
        closeModal()
      })
      .catch((err) => {
        setError(err.message)
        setIsLoading(false)
      })
  }

  return (
    <form onSubmit={handleSubmit}>
      <InputGroup
        inputProps={{ className: 'full-width' }}
        title="Name"
        value={name}
        onChange={(e) => setName(Utils.safeParseEventValue(e))}
      />
      {error && <ErrorMessage error={error} />}
      <Button type="submit" disabled={isLoading}>
        Submit
      </Button>
    </form>
  )
}
```

## Form Components (Global Scope)

These components are available globally (defined in global.d.ts):

- **InputGroup**: Standard input wrapper with label
  - `title` - Label text
  - `value` - Input value
  - `onChange` - Change handler
  - `inputProps` - Additional input attributes
- **Input**: Basic input element
- **Select**: Dropdown select (uses react-select)
- **Switch**: Toggle switch component
- **Button**: Standard button with theme support

## RTK Query Mutations Pattern

```typescript
import { useCreateFeatureMutation } from 'common/services/useFeature'

const MyForm: FC = () => {
  const [name, setName] = useState('')
  const [createFeature, { isLoading, error }] = useCreateFeatureMutation()

  const handleSubmit = async (e: React.FormEvent) => {
    Utils.preventDefault(e)

    try {
      await createFeature({ name, project_id: projectId }).unwrap()
      toast('Feature created!')
      closeModal()
    } catch (err) {
      toast('Error creating feature')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <InputGroup
        title="Feature Name"
        value={name}
        onChange={(e) => setName(Utils.safeParseEventValue(e))}
      />
      {error && <ErrorMessage error={error} />}
      <Button type="submit" disabled={isLoading}>
        Create
      </Button>
    </form>
  )
}
```

## Examples

Reference existing forms in the codebase:
- `web/components/SamlForm.js` - Class component form
- `web/components/modals/CreateSegmentRulesTabForm.tsx` - Complex form with state
- Search for `InputGroup` usage in `/web/components/` for more examples
