# UI Patterns & Best Practices

## Confirmation Dialogs

**NEVER use `window.confirm`** - Always use the `openConfirm` function from `components/base/Modal`.

### Correct Usage

```typescript
import { openConfirm } from 'components/base/Modal'

// Signature: openConfirm(title, body, onYes, onNo?, challenge?)
openConfirm(
  'Delete Partner',
  'Are you sure you want to delete this partner?',
  async (closeModal) => {
    const res = await deleteAction()
    if (!res.error) {
      toast(null, 'Partner deleted successfully')
      closeModal() // Always call closeModal to dismiss the dialog
    }
  },
)
```

### Parameters
- `title: string` - Dialog title
- `body: ReactNode` - Dialog content (can be JSX)
- `onYes: (closeModal: () => void) => void` - Callback when user confirms
- `onNo?: () => void` - Optional callback when user cancels
- `challenge?: string` - Optional challenge text user must type to confirm

### Key Points
- The `onYes` callback receives a `closeModal` function
- Always call `closeModal()` when the action completes successfully
- Can be async - use `async (closeModal) => { ... }`

## Backend Integration

### Always Run API Types Sync Before API Work

When using `/api` to generate new API services, the command automatically runs `/api-types-sync` first to:
1. Pull latest backend changes (`git pull` in `../api`)
2. Sync frontend types with backend serializers
3. Ensure types are up-to-date before generating new services

This prevents type mismatches and ensures consistency.
