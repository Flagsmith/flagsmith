import { ReactNode } from 'react'

// PoC (spike): in-tree modal state.
//
// Replaces the per-root `createRoot` plumbing that lived in Modal.tsx. The
// public API (openModal/openModal2/openConfirm) keeps its exact signatures, so
// the ~177 call sites and the window.* wiring in main.js are untouched. Opening
// a modal now pushes a descriptor here; the in-tree <ModalManager> renders it
// under the app's existing <Provider>, so modals inherit the store/theme/router
// context instead of each root re-creating a <Provider store={getStore()}>.
//
// Default modals are held as a stack, so "modal on modal" (the old openModal2)
// is just depth 2 of the same list rather than a bespoke second root.

export type ConfirmParams = {
  title: ReactNode
  body: ReactNode
  onYes: () => void
  onNo?: () => void
  destructive?: boolean
  yesText?: string
  noText?: string
}

export type ModalEntry = {
  key: number
  title: string
  body: ReactNode
  className?: string
  onClose?: () => void
  variant?: 'modal' | 'drawer'
}

export type ConfirmEntry = { key: number } & ConfirmParams

export type ModalState = {
  modals: ModalEntry[]
  confirm: ConfirmEntry | null
}

let state: ModalState = { confirm: null, modals: [] }
let key = 0
const listeners = new Set<() => void>()

const emit = () => {
  listeners.forEach((listener) => listener())
}

export const subscribeModals = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

// Returns a stable reference between changes so useSyncExternalStore is happy.
export const getModalState = () => state

export const openModal = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  // Opening the main modal resets the stack; fire onClose for anything dropped.
  state.modals.forEach((entry) => entry.onClose?.())
  state = {
    ...state,
    modals: [{ body, className, key: ++key, onClose, title }],
  }
  emit()
}

export const openModal2 = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  // Push on top of the current stack (the old "modal on modal").
  state = {
    ...state,
    modals: [...state.modals, { body, className, key: ++key, onClose, title }],
  }
  emit()
}

// Open a right-anchored Drawer (the modern replacement for the 'side-modal'
// className). Same shape as openModal; the className now only carries layout
// hooks (create-feature-modal, p-0, ...), not the side-modal routing string.
export const openDrawer = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  state.modals.forEach((entry) => entry.onClose?.())
  state = {
    ...state,
    modals: [
      { body, className, key: ++key, onClose, title, variant: 'drawer' },
    ],
  }
  emit()
}

export const openConfirm = (params: ConfirmParams) => {
  state = { ...state, confirm: { key: ++key, ...params } }
  emit()
}

export const closeModalByKey = (modalKey: number) => {
  const modals = state.modals.filter((entry) => entry.key !== modalKey)
  if (modals.length === state.modals.length) return
  state = { ...state, modals }
  emit()
}

export const clearConfirm = () => {
  if (!state.confirm) return
  state = { ...state, confirm: null }
  emit()
}

// Unsaved-changes guard: a modal registers a gate that runs before it closes.
// Lives here (not on ModalDefault) so the in-tree manager can honour it.
export let interceptClose: (() => Promise<boolean>) | null = null
export const setInterceptClose = (fn: (() => Promise<any>) | null) => {
  interceptClose = fn
}

// Dynamic title: the active modal registers a setter; setModalTitle updates it.
let titleSetter: ((title: ReactNode) => void) | null = null
export const registerModalTitleSetter = (
  fn: ((title: ReactNode) => void) | null,
) => {
  titleSetter = fn
}
export const setModalTitle = (title: ReactNode) => {
  titleSetter?.(title)
}

// Close the modal at a stack index, honouring the unsaved-changes guard on the
// main modal. Powers both the imperative closeModal()/closeModal2() globals and
// each dialog's own dismiss (Esc / backdrop / close button).
export const requestCloseModal = async (index: number) => {
  const entry = state.modals[index]
  if (!entry) return
  if (index === 0 && interceptClose) {
    const shouldClose = await interceptClose()
    if (!shouldClose) return
    setInterceptClose(null)
  }
  entry.onClose?.()
  closeModalByKey(entry.key)
}

// Legacy call sites reach these via window.openModal* (wired in main.js) and
// bare globals set up in project-components.js. closeModal/closeModal2 are
// referenced bare during render across the app, so they are stable functions
// defined once at load (never per-modal) that target the current stack — this
// avoids a ReferenceError when nothing is open and keeps captured handlers live.
const legacyGlobal = global as typeof globalThis & {
  openModal: typeof openModal
  openModal2: typeof openModal2
  openDrawer: typeof openDrawer
  openConfirm: typeof openConfirm
  closeModal: () => void
  closeModal2: () => void
}
legacyGlobal.openModal = openModal
legacyGlobal.openModal2 = openModal2
legacyGlobal.openDrawer = openDrawer
legacyGlobal.openConfirm = openConfirm
legacyGlobal.closeModal = () => {
  requestCloseModal(0)
}
legacyGlobal.closeModal2 = () => {
  requestCloseModal(1)
}
