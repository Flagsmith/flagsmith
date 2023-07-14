module.exports = function Component(options) {
  // eslint-disable-next-line
  return React.createClass(
    Object.assign({}, options, {
      _listeners: [],
      componentWillUnmount() {
        _.each(this._listeners, (listener, index) => {
          listener && this.stopListening(index)
        })
        return options.componentWillUnmount
          ? options.componentWillUnmount()
          : true
      },
      listenTo(store, event, callback) {
        this._listeners.push({
          callback,
          event,
          store,
        })
        store.on(event, callback)
        return this._listeners.length
      },

      req(val) {
        return val ? 'validate valid' : 'validate invalid'
      },

      setPathState(path, e) {
        return _.partial(() => {
          const newState = {}
          newState[path] = Utils.safeParseEventValue(e)
          this.setState(newState)
        })
      },

      setTheme(theme) {
        window.theme = theme

        this.forceUpdate()
      },

      stopListening(index) {
        const listener = this._listeners[index]
        listener.store.off(listener.event, listener.callback)
      },

      toggleState(path) {
        return _.partial(() => {
          const newState = {}
          newState[path] = !this.state[path]
          this.setState(newState)
        })
      },
    }),
  )
}
