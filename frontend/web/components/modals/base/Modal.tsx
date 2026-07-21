import {
  Modal as _Modal,
  ModalBody as _ModalBody,
  ModalFooter as _ModalFooter,
  ModalHeader as _ModalHeader,
  ModalProps,
} from 'reactstrap'
import { JSXElementConstructor, ReactNode, useCallback, useState } from 'react'
import { createRoot, Root } from 'react-dom/client'
import Confirm from './ModalConfirm'
import ModalDefault, { interceptClose, setInterceptClose } from './ModalDefault'
import { getStore } from 'common/store'
import { Provider } from 'react-redux'

type OpenConfirmParams = {
  title: ReactNode
  body: ReactNode
  onYes: () => void
  onNo?: () => void
  destructive?: boolean
  yesText?: string
  noText?: string
}

export const ModalHeader = _ModalHeader
export const ModalFooter = _ModalFooter
export const Modal = _Modal
export const ModalBody = _ModalBody

const withModal = (
  WrappedComponent: JSXElementConstructor<any>,
  {
    closePointer = 'closeModal',
    shouldInterceptClose = false,
  }: {
    closePointer?: string
    shouldInterceptClose?: boolean
  } = {},
) => {
  return (props: ModalProps) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [isOpen, setIsOpen] = useState(true)
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const toggle = useCallback(() => {
      if (interceptClose && shouldInterceptClose) {
        interceptClose().then((result) => {
          if (result) {
            setIsOpen(false)
            setInterceptClose(null)
          }
        })
      } else {
        setIsOpen(false)
      }
    }, [setIsOpen])
    // @ts-ignore
    global[closePointer] = toggle

    const onClosed = () => {
      if (props.onClosed) {
        props.onClosed()
      }
    }

    return (
      <Provider store={getStore()}>
        <WrappedComponent
          toggle={toggle}
          {...props}
          isOpen={isOpen}
          onClosed={onClosed}
        />
      </Provider>
    )
  }
}

function getOrCreateRoot(
  elementId: string,
  rootRef: { current: Root | null },
): Root {
  if (!rootRef.current) {
    const el = document.getElementById(elementId)
    if (!el) throw new Error(`Element #${elementId} not found`)
    rootRef.current = createRoot(el)
  }
  return rootRef.current
}

let modalKey = 0
let pendingModalOnClose: (() => void) | null = null
let pendingModal2OnClose: (() => void) | null = null

const confirmRootRef: { current: Root | null } = { current: null }
const modalRootRef: { current: Root | null } = { current: null }
const modal2RootRef: { current: Root | null } = { current: null }

const _Confirm = withModal(Confirm)
const _ModalDefault2 = withModal(ModalDefault, { closePointer: 'closeModal2' })
const _ModalDefault = withModal(ModalDefault, { shouldInterceptClose: true })

export const openConfirm = (global.openConfirm = ({
  body,
  destructive,
  noText,
  onNo,
  onYes,
  title,
  yesText,
}: OpenConfirmParams) => {
  const root = getOrCreateRoot('confirm', confirmRootRef)
  root.render(
    <_Confirm
      key={++modalKey}
      isOpen
      isDanger={destructive}
      onNo={onNo}
      onYes={onYes}
      title={title}
      yesText={yesText}
      noText={noText}
    >
      {body}
    </_Confirm>,
  )
})

export const openModal = (global.openModal = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  // If replacing a modal before its close transition completes, fire its
  // onClosed callback now since the transition will never finish.
  if (pendingModalOnClose) {
    pendingModalOnClose()
  }
  pendingModalOnClose = onClose ?? null
  const root = getOrCreateRoot('modal', modalRootRef)
  root.render(
    <_ModalDefault
      key={++modalKey}
      isOpen
      className={className}
      onClosed={() => {
        pendingModalOnClose = null
        onClose?.()
      }}
      title={title}
    >
      {body}
    </_ModalDefault>,
  )
})

//This is used when we show modals on top of modals, the UI pattern should be avoided if possible
export const openModal2 = (global.openModal2 = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  if (pendingModal2OnClose) {
    pendingModal2OnClose()
  }
  pendingModal2OnClose = onClose ?? null
  const root = getOrCreateRoot('modal2', modal2RootRef)
  root.render(
    <_ModalDefault2
      key={++modalKey}
      isOpen
      className={className}
      onClosed={() => {
        pendingModal2OnClose = null
        onClose?.()
      }}
      title={title}
    >
      {body}
    </_ModalDefault2>,
  )
})
