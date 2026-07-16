import {
  Modal as _Modal,
  ModalBody as _ModalBody,
  ModalFooter as _ModalFooter,
  ModalHeader as _ModalHeader,
} from 'reactstrap'

export const ModalHeader = _ModalHeader
export const ModalFooter = _ModalFooter
export const Modal = _Modal
export const ModalBody = _ModalBody

// PoC (spike): modal opening is delegated to the in-tree controller/manager
// instead of the old per-root createRoot plumbing. Signatures are unchanged,
// so call sites and the window.openModal* wiring in main.js keep working.
export { openModal, openModal2, openConfirm } from './modalController'
export type { ConfirmParams } from './modalController'
