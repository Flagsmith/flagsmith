import {
  FC,
  ReactNode,
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
} from 'react'
import Dialog, { ConfirmDialog, DialogSize } from 'components/base/Dialog'
import Drawer from 'components/base/Drawer'
import {
  clearConfirm,
  closeModalByKey,
  ConfirmEntry,
  getModalState,
  interceptClose,
  ModalEntry,
  ModalState,
  registerModalTitleSetter,
  setInterceptClose,
  subscribeModals,
} from './modalController'

// PoC (spike): renders the imperative modal stack with the DS Dialog (native
// <dialog>, top layer). Mounted once from App.js under the store <Provider>.

const legacyGlobal = global as typeof globalThis &
  Record<'closeModal' | 'closeModal2', (() => void) | undefined>

// Map the legacy openModal className to a Dialog size.
const sizeFor = (className?: string): DialogSize => {
  if (!className) return 'md'
  if (className.includes('modal-full-screen')) return 'full'
  if (className.includes('modal-lg')) return 'lg'
  if (className.includes('modal-sm')) return 'sm'
  return 'md'
}

const ModalSlot: FC<{ entry: ModalEntry; index: number }> = ({
  entry,
  index,
}) => {
  const [title, setTitle] = useState<ReactNode>(entry.title)

  // The main modal (index 0) owns the dynamic-title setter, matching the old
  // ModalDefault behaviour.
  useEffect(() => {
    if (index !== 0) return undefined
    registerModalTitleSetter(setTitle)
    return () => registerModalTitleSetter(null)
  }, [index])

  const requestClose = useCallback(async () => {
    // Only the main modal runs the unsaved-changes guard.
    if (index === 0 && interceptClose) {
      const shouldClose = await interceptClose()
      if (!shouldClose) return
      setInterceptClose(null)
    }
    entry.onClose?.()
    closeModalByKey(entry.key)
  }, [entry, index])

  // Keep the imperative globals working (closeModal()/closeModal2()).
  useEffect(() => {
    const pointer = (['closeModal', 'closeModal2'] as const)[index]
    if (!pointer) return undefined
    legacyGlobal[pointer] = requestClose
    return () => {
      if (legacyGlobal[pointer] === requestClose) {
        legacyGlobal[pointer] = undefined
      }
    }
  }, [index, requestClose])

  // Legacy side-modal maps to the Drawer; everything else is a centred Dialog.
  if (entry.className?.includes('side-modal')) {
    return (
      <Drawer
        open
        width={entry.className.includes('narrow') ? 'narrow' : 'default'}
        className={entry.className}
        onClose={requestClose}
      >
        <Drawer.Header>{title}</Drawer.Header>
        <Drawer.Body>{entry.body}</Drawer.Body>
      </Drawer>
    )
  }

  return (
    <Dialog
      open
      size={sizeFor(entry.className)}
      className={entry.className}
      onClose={requestClose}
    >
      <Dialog.Header>{title}</Dialog.Header>
      <Dialog.Body>{entry.body}</Dialog.Body>
    </Dialog>
  )
}

const ConfirmSlot: FC<{ entry: ConfirmEntry }> = ({ entry }) => {
  const no = () => {
    entry.onNo?.()
    clearConfirm()
  }
  const yes = () => {
    entry.onYes?.()
    clearConfirm()
  }
  return (
    <ConfirmDialog
      open
      title={entry.title}
      destructive={entry.destructive}
      yesText={entry.yesText}
      noText={entry.noText}
      onYes={yes}
      onNo={no}
    >
      {entry.body}
    </ConfirmDialog>
  )
}

const ModalManager: FC = () => {
  const state: ModalState = useSyncExternalStore(subscribeModals, getModalState)
  return (
    <>
      {state.modals.map((entry, index) => (
        <ModalSlot key={entry.key} entry={entry} index={index} />
      ))}
      {state.confirm && (
        <ConfirmSlot key={state.confirm.key} entry={state.confirm} />
      )}
    </>
  )
}

export default ModalManager
