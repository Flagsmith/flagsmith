# UI Patterns & Best Practices

**Use design tokens, utility classes, and primitive components before writing anything custom.** Each tier composes the one below — pick the highest tier that fits before reaching for SCSS.

## Design Tokens & Primitives

### Colour Tokens

**Location:** `common/theme/tokens.ts` (auto-generated from `common/theme/tokens.json`)

Never hardcode hex colours in TSX or SCSS. Use:
- **In SCSS:** CSS variables directly — `var(--color-text-success)`, `var(--color-border-action)`, `var(--color-surface-muted)`
- **In TSX (inline styles / chart props):** JS token constants — `colorTextSuccess`, `colorBorderAction`, `colorSurfaceMuted`

Token categories: `colorText*`, `colorIcon*`, `colorBorder*`, `colorSurface*`, `colorChart*`, `radius*`, `shadow*`, `duration*`, `easing*`.

### Utility Classes

Before writing custom SCSS, check for token-driven utilities:

- **Token utilities** (`web/styles/_token-utilities.scss`): `bg-surface-*`, `text-*`, `border-*`, `rounded-*`, `shadow-*`, `transition-*`
- **Bootstrap utilities** (layout / spacing): `d-flex`, `flex-column`, `gap-*`, `p-*`, `m-*`, `text-center`, `align-items-*`, `justify-content-*`

Prefer utility classes over one-off SCSS rules. Combine them freely — `className='d-flex gap-3 bg-surface-muted rounded-lg p-3'`.

### Primitive Components — Use Before Building

Before creating a custom element, check if an existing primitive fits:

| Need | Primitive | Location |
|------|-----------|----------|
| Coloured dot / swatch | `ColorSwatch` | `components/ColorSwatch.tsx` — accepts `color`, `size` (`sm`/`md`/`lg`), `shape` (`square`/`circle`) |
| Text input | `Input` | `components/base/forms/Input.js` — has `search` prop for built-in search icon |
| Labelled field (text, textarea) | `InputGroup` | `components/base/forms/InputGroup.js` — has `textarea` prop, `title`, handles label + layout |
| Icons | `Icon` | `components/icons/Icon.tsx` — project's own icon set. **Never use external icon libraries** (ionicons, etc.) |
| Confirm dialog | `openConfirm` | `components/base/Modal` — see Confirmation Dialogs section below |

### Inline Styles

Avoid inline `style={}` props. Acceptable exceptions:
- Flex layout fixes (`minWidth: 0` for overflow prevention)
- Dynamic values that genuinely vary at runtime (e.g. chart dimensions)

For fixed dimensions (widths, padding), prefer SCSS classes.

## Code Organisation

### Component File Structure

Multi-file components (TSX + SCSS) use a folder structure with a barrel export:

```
ComponentName/
├── ComponentName.tsx
├── ComponentName.scss
└── index.ts          ← barrel export
```

Single-file components without their own styles can live as a single `.tsx` next to peers — no folder needed.

## Storybook (Optional)

When working on complex or unfamiliar components, you can query Storybook MCP (`list-all-documentation`, then `get-documentation`) to discover existing components, their props, and visual examples. This is optional — for simple changes, grepping the codebase is fine.

## Table Components

### Pattern: Reusable Table Components

**Location:** `components/project/tables/`

Tables should be self-contained components that fetch their own data and handle loading/error states.

**Example:** `InvoiceTable.tsx`

```typescript
import { useGetInvoicesQuery } from 'common/services/useInvoice'
import { useDefaultSubscription } from 'common/services/useDefaultSubscription'
import Loader from 'components/base/Loader'
import { ErrorMessage } from 'components/base/Messages'
import ContentContainer from './ContentContainer'

const InvoiceTable: FC = () => {
  const { defaultSubscriptionId } = useDefaultSubscription()
  const { data: invoices, error, isLoading } = useGetInvoicesQuery({
    subscription_id: `${defaultSubscriptionId}`,
  })

  if (isLoading) {
    return (
      <div className='d-flex justify-content-center'>
        <Loader />
      </div>
    )
  }

  if (error) return <ErrorMessage>{error}</ErrorMessage>

  return (
    <ContentContainer>
      <table className='invoice-table'>
        <thead>
          <tr>
            <th>Invoice No.</th>
            <th className='d-none d-md-table-cell'>Description</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {invoices?.map((invoice) => (
            <tr key={invoice.id}>
              <td>{invoice.id}</td>
              <td className='d-none d-md-table-cell'>{invoice.description}</td>
              <td>{invoice.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </ContentContainer>
  )
}
```

### Responsive Tables

Use Bootstrap classes for responsive behavior:
- `d-none d-md-table-cell` - Hide column on mobile
- `d-block d-md-none` - Show on mobile only

## Tabs Component

**Location:** `components/navigation/TabMenu/Tabs.tsx`

### Basic Usage

```typescript
import { useState } from 'react'
import { Tabs } from 'components/base/forms/Tabs'

const MyPage = () => {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <Tabs
      value={activeTab}
      onChange={setActiveTab}
      tabLabels={['Tab 1', 'Tab 2', 'Tab 3']}
    >
      <div>Tab 1 content</div>
      <div>Tab 2 content</div>
      <div>Tab 3 content</div>
    </Tabs>
  )
}
```

### Tabs with Feature Flag (Optional)

**Note:** Only use feature flags when explicitly requested. By default, implement features directly without flags.

When specifically requested, this pattern shows tabs only when feature flag is enabled:

```typescript
import { useFlags } from '@flagsmith/flagsmith/react'
import { Tabs } from 'components/base/forms/Tabs'
import Utils from 'common/utils/utils'
const MyPage = () => {
  const my_feature_flag = Utils.getFlagsmithHasFeature('my_feature_flag')
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div>
      <h2>My Section</h2>
      {my_feature_flag? (
        <Tabs
          value={activeTab}
          onChange={setActiveTab}
          tabLabels={['Default', 'New Feature']}
        >
          <div><ExistingComponent /></div>
          <div><NewComponent /></div>
        </Tabs>
      ) : (
        <ExistingComponent />
      )}
    </div>
  )
}
```

See `feature-flags/` for more details on when and how to use feature flags.

### Uncontrolled Tabs

For simple cases without parent state management:

```typescript
<Tabs uncontrolled tabLabels={['Tab 1', 'Tab 2']}>
  <div>Tab 1 content</div>
  <div>Tab 2 content</div>
</Tabs>
```

## Confirmation Dialogs

**NEVER use `window.confirm`** - Always use the `openConfirm` function from `components/base/Modal`.

### Correct Usage

```typescript
import { openConfirm } from 'components/base/Modal'

// Signature: openConfirm(title, body, onYes, onNo?, challenge?)
openConfirm({
    body: 'Closing this will discard your unsaved changes.',
    noText: 'Cancel',
    onNo: () => resolve(false),
    onYes: () => resolve(true),
    title: 'Discard changes',
    yesText: 'Ok',
})
```

### Parameters
- `title: ReactNode` - Dialog title
- `body: ReactNode` - Dialog content (can be JSX)
- `onYes: () => void` - Callback when user confirms. The modal closes automatically after `onYes` returns.
- `onNo?: () => void` - Optional callback when user cancels
- `yesText?: string` - Label for the confirm button (default "OK")
- `noText?: string` - Label for the cancel button (default "Cancel")
- `destructive?: boolean` - Renders the confirm button in danger styling. Use for delete/discard actions.
