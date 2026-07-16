import { MouseEvent, SyntheticEvent, useEffect, useRef } from 'react'

// Shared native <dialog> mechanics for Dialog and Drawer:
// - imperative open/close driven by `open` (showModal promotes to the top layer)
// - Esc + backdrop-click dismissal
// - the app's `.modal-open` body class (scroll lock, hides the support chat),
//   ref-counted so stacked dialogs don't clear it early.
let openDialogs = 0

export const useNativeDialog = (open: boolean, onClose: () => void) => {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    openDialogs += 1
    document.body.classList.add('modal-open')
    return () => {
      openDialogs -= 1
      if (openDialogs <= 0) {
        openDialogs = 0
        document.body.classList.remove('modal-open')
      }
    }
  }, [open])

  return {
    onCancel: (e: SyntheticEvent<HTMLDialogElement>) => {
      // Esc: run our onClose rather than the browser's immediate close.
      e.preventDefault()
      onClose()
    },
    onClick: (e: MouseEvent<HTMLDialogElement>) => {
      // A click landing on the dialog element itself is a backdrop click.
      if (e.target === ref.current) onClose()
    },
    ref,
  }
}
