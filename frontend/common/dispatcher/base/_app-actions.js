module.exports = {
  login(details) {
    // refresh the entire app
    Dispatcher.handleViewAction({
      actionType: Actions.LOGIN,
      details,
    })
  },
  logout() {
    // refresh the entire app
    Dispatcher.handleViewAction({
      actionType: Actions.LOGOUT,
    })
  },
  refresh() {
    // refresh the entire app
    Dispatcher.handleViewAction({
      actionType: Actions.REFRESH,
    })
  },
  register(details, isInvite) {
    // refresh the entire app
    Dispatcher.handleViewAction({
      actionType: Actions.REGISTER,
      details,
      isInvite,
    })
  },
  registerNotifications(data) {
    Dispatcher.handleViewAction({
      actionType: Actions.REGISTER_NOTIFICATIONS,
      data,
    })
  },
  setToken(token) {
    Dispatcher.handleViewAction({
      actionType: Actions.SET_TOKEN,
      token,
    })
  },
  setUser(user) {
    Dispatcher.handleViewAction({
      actionType: Actions.SET_USER,
      user,
    })
  },
}
