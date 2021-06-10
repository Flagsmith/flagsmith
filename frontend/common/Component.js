module.exports = function (options) {
    return React.createClass(Object.assign({}, options, {
        _listeners: [],
        setTheme(theme) {
            window.theme = theme;

            this.forceUpdate();
        },
        listenTo(store, event, callback) {
            this._listeners.push({
                store,
                event,
                callback,
            });
            store.on(event, callback);
            return this._listeners.length;
        },

        stopListening(index) {
            const listener = this._listeners[index];
            listener.store.off(listener.event, listener.callback);
        },

        req(val) {
            return val ? 'validate valid' : 'validate invalid';
        },

        setPathState(path, e) {
            return _.partial(() => {
                const newState = {};
                newState[path] = Utils.safeParseEventValue(e);
                this.setState(newState);
            });
        },

        toggleState(path) {
            return _.partial(() => {
                const newState = {};
                newState[path] = !this.state[path];
                this.setState(newState);
            });
        },

        componentWillUnmount() {
            _.each(this._listeners, (listener, index) => {
                listener && this.stopListening(index);
            });
            return options.componentWillUnmount ? options.componentWillUnmount() : true;
        },
    }));
};
