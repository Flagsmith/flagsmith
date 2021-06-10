module.exports = {
    getConfig() { // get upcoming routes
        Dispatcher.handleViewAction({
            actionType: Actions.GET_CONFIG,
        });
    },
    refresh() { // refresh the entire app
        Dispatcher.handleViewAction({
            actionType: Actions.REFRESH,
        });
    },
    registerNotifications(data) {
        Dispatcher.handleViewAction({
            actionType: Actions.REGISTER_NOTIFICATIONS,
            data,
        });
    },
    setUser(user) {
        Dispatcher.handleViewAction({
            actionType: Actions.SET_USER,
            user,
        });
    },
    setToken(token) {
        Dispatcher.handleViewAction({
            actionType: Actions.SET_TOKEN,
            token,
        });
    },
    register(details, isInvite) { // refresh the entire app
        Dispatcher.handleViewAction({
            actionType: Actions.REGISTER,
            details,
            isInvite,
        });
    },
    login(details) { // refresh the entire app
        Dispatcher.handleViewAction({
            actionType: Actions.LOGIN,
            details,
        });
    },
    logout() { // refresh the entire app
        Dispatcher.handleViewAction({
            actionType: Actions.LOGOUT,
        });
    },
};
