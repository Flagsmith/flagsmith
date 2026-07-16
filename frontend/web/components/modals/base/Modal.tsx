// Modal opening is delegated to the in-tree controller/manager, which renders
// the native-<dialog> DS Dialog/Drawer. reactstrap is no longer used anywhere.
// Signatures are unchanged, so call sites and the window.openModal* wiring in
// main.js keep working.
export {
  openModal,
  openModal2,
  openDrawer,
  openConfirm,
} from './modalController'
export type { ConfirmParams } from './modalController'
