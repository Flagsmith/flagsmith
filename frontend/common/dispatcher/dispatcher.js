import ReactDispatcher from 'flux-react-dispatcher'

const Dispatcher = new ReactDispatcher()

const theDispatcher = Object.assign(Dispatcher, {
  handleViewAction(action) {
    const payload = {
      action,
      source: 'VIEW_ACTION',
    }

    this.dispatch(payload)
  },
})

window.Dispatcher = Dispatcher
export default theDispatcher
