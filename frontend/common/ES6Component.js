module.exports = function (context, onUnmount) {
    context._listeners = [];

    context.listenTo = function (store, event, callback) {
        this._listeners.push({
            store,
            event,
            callback,
        });
        store.on(event, callback);
        return this._listeners.length;
    };

    context.stopListening = function (index) {
        const listener = this._listeners[index];
        listener.store.off(listener.event, listener.callback);
    };

    context.setTimedState = function (path, val, cooldown) { // set a temporary state, useful for showing things for a set amount of time
        const original = this.state[path];
        const state = {};
        if (original !== val) {
            state[path] = val;
            this.setState(state);
            setTimeout(() => {
                state[path] = original;
                this.setState(state);
            }, cooldown || 500);
        }
    };

    context.setPathState = function (path, e) {
        return _.partial(() => {
            const newState = {};
            newState[path] = Utils.safeParseEventValue(e);
            this.setState(newState);
        });
    };

    context.toggleState = function (path) {
        return _.partial(() => {
            const newState = {};
            newState[path] = !this.state[path];
            this.setState(newState);
        });
    };

    context.componentWillUnmount = function () {
        _.each(this._listeners, (listener, index) => {
            if (listener) this.stopListening(index);
        });
        if (onUnmount) {
            onUnmount.call(context);
        }
    };
};
