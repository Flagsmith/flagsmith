const EventEmitter = require('events').EventEmitter;

const DEFAULT_CHANGE_EVENT = 'change';


const DEFAULT_LOADING_EVENT = 'loading';


const DEFAULT_LOADED_EVENT = 'loaded';


const DEFAULT_SAVED_EVENT = 'saved';


const DEFAULT_SAVING_EVENT = 'saving';


const DEFAULT_ERROR_EVENT = 'problem';

module.exports = Object.assign({}, EventEmitter.prototype, {
    _maxListeners: Number.MAX_VALUE,
    id: '',
    isLoading: false,
    hasLoaded: false,
    isSaving: false,
    subscriptions: {},

    trigger(eventName, data) {
        this.emit(eventName || DEFAULT_CHANGE_EVENT, data);
    },

    loading() {
        this.hasLoaded = false;
        this.isLoading = true;
        this.trigger(DEFAULT_CHANGE_EVENT);
        this.trigger(DEFAULT_LOADING_EVENT);
    },

    saving() {
        this.isSaving = true;
        this.trigger(DEFAULT_CHANGE_EVENT);
        this.trigger(DEFAULT_SAVING_EVENT);
    },

    loaded() {
        this.hasLoaded = true;
        this.isLoading = false;
        this.trigger(DEFAULT_LOADED_EVENT);
        this.trigger(DEFAULT_CHANGE_EVENT);
    },

    changed() {
        // console.log('change', this.id)
        this.trigger(DEFAULT_CHANGE_EVENT);
    },

    saved() {
        this.isSaving = false;
        this.trigger(DEFAULT_SAVED_EVENT);
        this.trigger(DEFAULT_CHANGE_EVENT);
    },

    goneABitWest() {
        this.hasLoaded = true;
        this.isLoading = false;
        this.isSaving = false;
        this.trigger(DEFAULT_CHANGE_EVENT);
        this.trigger(DEFAULT_ERROR_EVENT);
    },

    on(eventName, callback) {
        this.addListener(eventName || DEFAULT_CHANGE_EVENT, callback);
    },

    off(eventName, callback) {
        this.removeListener(eventName || DEFAULT_CHANGE_EVENT, callback);
    },

});
