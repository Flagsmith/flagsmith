import {
  FC,
  ReactNode,
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
} from 'react'
import Dialog, { DialogSize } from 'components/base/Dialog'
import Button from 'components/base/forms/Button'
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

// Map the legacy openModal className to a Dialog size/variant.
const sizeFor = (className?: string): DialogSize => {
  if (!className) return 'md'
  if (className.includes('side-modal')) return 'side'
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
    <Dialog open size='sm' onClose={no}>
      <Dialog.Header>{entry.title}</Dialog.Header>
      <Dialog.Body>{entry.body}</Dialog.Body>
      <Dialog.Footer>
        <Button theme='secondary' id='confirm-btn-no' onClick={no}>
          {entry.noText ?? 'Cancel'}
        </Button>
        <Button
          theme={entry.destructive ? 'danger' : 'primary'}
          id='confirm-btn-yes'
          onClick={yes}
        >
          {entry.yesText ?? 'OK'}
        </Button>
      </Dialog.Footer>
    </Dialog>
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
