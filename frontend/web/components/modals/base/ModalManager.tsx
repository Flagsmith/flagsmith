import {
  FC,
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
} from 'react'
import ModalDefault from './ModalDefault'
import Confirm from './ModalConfirm'
import {
  clearConfirm,
  closeModalByKey,
  ConfirmEntry,
  getModalState,
  ModalEntry,
  ModalState,
  subscribeModals,
} from './modalController'

// PoC (spike): renders active modals in-tree via reactstrap's `container`
// prop pointed at #app, so the DOM lands inside the app root (not <body>) and
// context flows down. Mounted once from App.js inside the store <Provider>.

const legacyGlobal = global as typeof globalThis &
  Record<'closeModal' | 'closeModal2', (() => void) | undefined>

const ModalSlot: FC<{ entry: ModalEntry; index: number }> = ({
  entry,
  index,
}) => {
  const [isOpen, setIsOpen] = useState(true)
  const toggle = useCallback(() => setIsOpen(false), [])

  // Levels 0 and 1 keep the imperative globals working (closeModal/closeModal2).
  useEffect(() => {
    const pointer = (['closeModal', 'closeModal2'] as const)[index]
    if (!pointer) return
    legacyGlobal[pointer] = toggle
    return () => {
      if (legacyGlobal[pointer] === toggle) legacyGlobal[pointer] = undefined
    }
  }, [index, toggle])

  return (
    <ModalDefault
      container='app'
      isOpen={isOpen}
      zIndex={1050 + index * 20}
      title={entry.title}
      className={entry.className}
      toggle={toggle}
      onClosed={() => {
        entry.onClose?.()
        closeModalByKey(entry.key)
      }}
    >
      {entry.body}
    </ModalDefault>
  )
}

const ConfirmSlot: FC<{ entry: ConfirmEntry }> = ({ entry }) => {
  const [isOpen, setIsOpen] = useState(true)
  const toggle = useCallback(() => setIsOpen(false), [])
  return (
    <Confirm
      container='app'
      isOpen={isOpen}
      isDanger={entry.destructive}
      title={entry.title}
      yesText={entry.yesText}
      noText={entry.noText}
      onYes={entry.onYes}
      onNo={entry.onNo}
      toggle={toggle}
      onClosed={clearConfirm}
    >
      {entry.body}
    </Confirm>
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
