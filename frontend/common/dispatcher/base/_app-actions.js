export default {
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
  register(details, isInvite) {
    // refresh the entire app
    Dispatcher.handleViewAction({
      actionType: Actions.REGISTER,
      details,
      isInvite,
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
