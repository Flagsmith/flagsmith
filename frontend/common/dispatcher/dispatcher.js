const ReactDispatcher = require('flux-react-dispatcher');

const Dispatcher = new ReactDispatcher();

const theDispatcher = Object.assign(Dispatcher, {
    handleViewAction(action) {

        const payload = {
            source: 'VIEW_ACTION',
            action,
        };

        this.dispatch(payload);
    },

});

window.Dispatcher = Dispatcher;
module.exports = theDispatcher;
