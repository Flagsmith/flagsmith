import {
  Modal as _Modal,
  ModalBody as _ModalBody,
  ModalFooter as _ModalFooter,
  ModalHeader as _ModalHeader,
  ModalProps,
} from 'reactstrap'
import { JSXElementConstructor, ReactNode, useCallback, useState } from 'react'
import { render, unmountComponentAtNode } from 'react-dom'
import Confirm from './ModalConfirm'
import ModalDefault, { interceptClose, setInterceptClose } from './ModalDefault'
import { getStore } from 'common/store'
import { Provider } from 'react-redux'
import { OpenConfirm } from '../../../../global'

export const ModalHeader = _ModalHeader
export const ModalFooter = _ModalFooter
export const Modal = _Modal
export const ModalBody = _ModalBody

const withModal = (
  WrappedComponent: JSXElementConstructor<any>,
  { closePointer = 'closeModal', shouldInterceptClose = false } = {},
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

    return (
      <Provider store={getStore()}>
        <WrappedComponent toggle={toggle} {...props} isOpen={isOpen} />
      </Provider>
    )
  }
}

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
}: OpenConfirm) => {
  document.getElementById('confirm') &&
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    unmountComponentAtNode(document.getElementById('confirm')!)
  render(
    <_Confirm
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
    document.getElementById('confirm'),
  )
})

export const openModal = (global.openModal = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  document.getElementById('modal') &&
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    unmountComponentAtNode(document.getElementById('modal')!)
  render(
    <_ModalDefault
      isOpen
      className={className}
      onClosed={onClose}
      title={title}
    >
      {body}
    </_ModalDefault>,
    document.getElementById('modal'),
  )
})

//This is used when we show modals on top of modals, the UI pattern should be avoided if possible
export const openModal2 = (global.openModal2 = (
  title: string,
  body: ReactNode,
  className?: string,
  onClose?: () => void,
) => {
  document.getElementById('modal2') &&
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    unmountComponentAtNode(document.getElementById('modal2')!)
  render(
    <_ModalDefault2
      isOpen
      className={className}
      onClosed={onClose}
      title={title}
    >
      {body}
    </_ModalDefault2>,
    document.getElementById('modal2'),
  )
})
