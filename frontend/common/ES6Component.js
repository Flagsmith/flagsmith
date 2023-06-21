module.exports = function es6Component(context, onUnmount) {
  context._listeners = []

  context.listenTo = function listenTo(store, event, callback) {
    this._listeners.push({
      callback,
      event,
      store,
    })
    store.on(event, callback)
    return this._listeners.length
  }

  context.stopListening = function stopListening(index) {
    const listener = this._listeners[index]
    listener.store.off(listener.event, listener.callback)
  }

  context.setTimedState = function setTimedState(path, val, cooldown) {
    // set a temporary state, useful for showing things for a set amount of time
    const original = this.state[path]
    const state = {}
    if (original !== val) {
      state[path] = val
      this.setState(state)
      setTimeout(() => {
        state[path] = original
        this.setState(state)
      }, cooldown || 500)
    }
  }

  context.setPathState = function setPathState(path, e) {
    return _.partial(() => {
      const newState = {}
      newState[path] = Utils.safeParseEventValue(e)
      this.setState(newState)
    })
  }

  context.toggleState = function toggleState(path) {
    return _.partial(() => {
      const newState = {}
      newState[path] = !this.state[path]
      this.setState(newState)
    })
  }

  context.componentWillUnmount = function componentWillUnmount() {
    _.each(this._listeners, (listener, index) => {
      if (listener) this.stopListening(index)
    })
    if (onUnmount) {
      onUnmount.call(context)
    }
  }
}
