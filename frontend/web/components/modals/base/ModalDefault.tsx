// The reactstrap ModalDefault component has been retired: modals now render via
// the DS Dialog (native <dialog>) through ModalManager. The unsaved-changes
// guard and dynamic-title helpers live in the controller; re-exported here so
// the existing ~15 call sites keep importing them from this path.
export {
  interceptClose,
  setInterceptClose,
  setModalTitle,
} from './modalController'
