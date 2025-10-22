# UI Patterns & Best Practices

## Confirmation Dialogs

**NEVER use `window.confirm`** - Always use the `openConfirm` function from `components/base/Modal`.

### Correct Usage

```typescript
import { openConfirm } from 'components/base/Modal'

// Basic confirmation
openConfirm({
  title: 'Delete Item',
  body: 'Are you sure you want to delete this item?',
  onYes: () => {
    // Perform delete action
    deleteItem()
  },
})

// With custom button text and destructive styling
openConfirm({
  title: 'Discard changes',
  body: 'Closing this will discard your unsaved changes.',
  destructive: true,
  yesText: 'Discard',
  noText: 'Cancel',
  onYes: () => {
    // Discard changes
    closeWithoutSaving()
  },
  onNo: () => {
    // Optional: Handle cancel action
    console.log('User cancelled')
  },
})

// With JSX body
openConfirm({
  title: 'Delete User',
  body: (
    <div>
      {'Are you sure you want to delete '}
      <strong>{userName}</strong>
      {' from this organization?'}
    </div>
  ),
  destructive: true,
  onYes: async () => {
    // Can be async
    await deleteUser({ id: userId })
  },
})
```

### Parameters

- **title**: `ReactNode` (required) - Dialog title (can be string or JSX)
- **body**: `ReactNode` (required) - Dialog content (can be string or JSX)
- **onYes**: `() => void` (required) - Callback when user confirms (can be async)
- **onNo**: `() => void` (optional) - Callback when user cancels
- **destructive**: `boolean` (optional) - Makes the confirm button red/dangerous
- **yesText**: `string` (optional) - Custom text for confirm button (default: "Confirm")
- **noText**: `string` (optional) - Custom text for cancel button (default: "Cancel")

### Key Points

- The modal closes automatically after `onYes` or `onNo` is called
- You do NOT need to manually close the modal
- Use `destructive: true` for dangerous actions (delete, discard, etc.)
- Both `onYes` and `onNo` callbacks can be async
- The `body` can be a string or JSX element for rich content
- NEVER use `window.confirm` - always use this `openConfirm` function

## Custom Modals

Use `openModal` for displaying custom modal content:

```typescript
import { openModal } from 'components/base/Modal'

// Basic modal
openModal('Modal Title', <MyModalContent />)

// With custom class and close callback
openModal(
  'Settings',
  <SettingsForm />,
  'large-modal', // Optional className
  () => {
    // Optional: Called when modal closes
    console.log('Modal closed')
  }
)
```

### Parameters

- **title**: `ReactNode` (required) - Modal title
- **body**: `ReactNode` (optional) - Modal content
- **className**: `string` (optional) - CSS class for modal styling
- **onClose**: `() => void` (optional) - Callback when modal closes

### Nested Modals

For modals that need to open on top of other modals (avoid if possible):

```typescript
import { openModal2 } from 'components/base/Modal'

openModal2('Second Modal', <SecondaryContent />)
```

## Backend Integration

### Always Run API Types Sync Before API Work

When using `/api` to generate new API services, the command automatically runs `/api-types-sync` first to:
1. Compare latest backend changes in main
2. Sync frontend types with backend serializers
3. Ensure types are up-to-date before generating new services

This prevents type mismatches and ensures consistency.
