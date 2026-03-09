---
title: "Migrate modal system from global imperative API to React context"
labels: ["design-system", "large-refactor"]
status: DRAFT
---

## Problem

The modal system relies on a deprecated React 16-era imperative API that
attaches `openModal`, `openModal2`, `openConfirm`, and `closeModal` to the
`global`/`window` object. This is used across 46+ files.

### Specific issues

1. **Deprecated `ReactDOM.render` usage** — `web/components/modals/base/Modal.tsx`
   calls `render()` and `unmountComponentAtNode()` from `react-dom`, which are
   removed in React 18. This is the primary blocker for a React 18 upgrade.

2. **`openModal2` anti-pattern** — a second modal API was added alongside the
   original `openModal` to work around limitations, resulting in two competing
   global functions for the same task.

3. **14 near-identical confirmation modals** — each implements its own layout,
   button arrangement, and copy:
   - `ConfirmRemoveFeature.tsx`
   - `ConfirmRemoveSegment.tsx`
   - `ConfirmRemoveProject.tsx`
   - `ConfirmRemoveOrganisation.tsx`
   - `ConfirmRemoveEnvironment.tsx`
   - `ConfirmRemoveWebhook.tsx`
   - `ConfirmRemoveAuditWebhook.tsx`
   - `ConfirmRemoveTrait.tsx`
   - `ConfirmDeleteAccount.tsx`
   - `ConfirmDeleteRole.tsx`
   - `ConfirmToggleFeature.tsx`
   - `ConfirmToggleEnvFeature.tsx`
   - `ConfirmHideFlags.tsx`
   - `ConfirmCloneSegment.tsx`

   These could be a single `ConfirmModal` component with configurable title,
   message, and action props.

4. **Legacy JS modals** — `CreateProject.js`, `CreateWebhook.js`, and
   `Payment.js` are class components in plain JavaScript, using `propTypes` and
   relying on the global registry.

5. **No context for modal state** — because modals are rendered imperatively into
   a detached DOM node, they cannot access React context (e.g. Redux store)
   without the `<Provider>` wrapper that `Modal.tsx` manually injects.

## Files

- `web/components/modals/base/Modal.tsx` — imperative `openModal`/`closeModal`
  implementation using `ReactDOM.render`
- `web/components/modals/base/ModalDefault.tsx` — default modal wrapper
- `web/components/modals/base/ModalConfirm.tsx` — confirmation modal base
- `web/components/modals/Confirm*.tsx` — 14 confirmation modal variants
- `web/components/modals/CreateProject.js` — legacy JS class component
- `web/components/modals/CreateWebhook.js` — legacy JS class component (duplicate
  of `CreateWebhook.tsx`)
- `web/components/modals/Payment.js` — legacy JS class component
- 46+ files across `web/components/` that call `openModal` or `openModal2`

## Proposed Fix

### Step 1 — Create ModalProvider context

```tsx
// web/components/modals/ModalProvider.tsx
const ModalContext = createContext<ModalContextValue>(null)

export const ModalProvider: FC<PropsWithChildren> = ({ children }) => {
  const [modals, setModals] = useState<ModalEntry[]>([])
  // open, close, confirm methods
  return (
    <ModalContext.Provider value={{ open, close, confirm }}>
      {children}
      {modals.map(modal => <ModalRenderer key={modal.id} {...modal} />)}
    </ModalContext.Provider>
  )
}

export const useModal = () => useContext(ModalContext)
```

### Step 2 — Consolidate confirmation modals

Create a single `ConfirmModal` component that accepts:
- `title: string`
- `message: ReactNode`
- `confirmText?: string` (default: "Confirm")
- `cancelText?: string` (default: "Cancel")
- `onConfirm: () => void | Promise<void>`
- `variant?: 'danger' | 'warning' | 'default'`

Replace all 14 `Confirm*.tsx` files with call sites that use:
```tsx
const { confirm } = useModal()
confirm({
  title: 'Remove Feature',
  message: `Are you sure you want to remove "${name}"?`,
  variant: 'danger',
  onConfirm: handleDelete,
})
```

### Step 3 — Migrate call sites from global to hook

For each of the 46+ files that call `openModal`/`openModal2`:
1. Import `useModal`
2. Replace `openModal(...)` with `modal.open(...)`
3. Remove any `global.openModal` references

### Step 4 — Remove legacy imperative API

Once all call sites are migrated:
1. Remove `ReactDOM.render`/`unmountComponentAtNode` calls from `Modal.tsx`
2. Remove `openModal`, `openModal2`, `closeModal` from `global`/`window`
3. Delete the legacy JS modal files (`CreateProject.js`, `CreateWebhook.js`,
   `Payment.js`)

## Acceptance Criteria

- [ ] `ModalProvider` context exists and is mounted at the app root
- [ ] A single `ConfirmModal` component replaces all 14 confirmation variants
- [ ] No `openModal`, `openModal2`, or `closeModal` on `global`/`window`
- [ ] No `ReactDOM.render` or `unmountComponentAtNode` calls remain in modal code
- [ ] All modals have access to React context (Redux store, theme) without
      manual `<Provider>` wrapping
- [ ] `CreateProject.js`, `CreateWebhook.js`, and `Payment.js` are deleted or
      converted to TypeScript
- [ ] `npm run typecheck` and `npm run build` pass
- [ ] E2E tests for modal flows (create feature, delete segment, etc.) pass

## Dependencies

- Related to **LR-9** (Remove global component registry) — that issue covers the
  broader `window.*` pattern; this issue focuses specifically on the modal globals
- Related to **LR-5** (JS to TypeScript) — the 3 legacy JS modals should be
  converted as part of this work
- Prerequisite for React 18 upgrade — `ReactDOM.render` must be removed first

---
Part of the Design System Audit (#6606)
