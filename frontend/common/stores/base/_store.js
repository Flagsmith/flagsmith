const EventEmitter = require('events').EventEmitter

const DEFAULT_CHANGE_EVENT = 'change'

const DEFAULT_LOADING_EVENT = 'loading'

const DEFAULT_LOADED_EVENT = 'loaded'

const DEFAULT_SAVED_EVENT = 'saved'

const DEFAULT_SAVING_EVENT = 'saving'

const DEFAULT_ERROR_EVENT = 'problem'

module.exports = Object.assign({}, EventEmitter.prototype, {
  _maxListeners: Number.MAX_VALUE,
  changed() {
    // console.log('change', this.id)
    this.trigger(DEFAULT_CHANGE_EVENT)
  },
  goneABitWest() {
    this.hasLoaded = true
    this.isLoading = false
    this.isSaving = false
    this.trigger(DEFAULT_CHANGE_EVENT)
    this.trigger(DEFAULT_ERROR_EVENT)
  },
  hasLoaded: false,
  id: '',
  isLoading: false,

  isSaving: false,

  loaded() {
    this.hasLoaded = true
    this.error = null
    this.isLoading = false
    this.trigger(DEFAULT_LOADED_EVENT)
    this.trigger(DEFAULT_CHANGE_EVENT)
  },

  loading() {
    this.hasLoaded = false
    this.isLoading = true
    this.trigger(DEFAULT_CHANGE_EVENT)
    this.trigger(DEFAULT_LOADING_EVENT)
  },

  off(eventName, callback) {
    this.removeListener(eventName || DEFAULT_CHANGE_EVENT, callback)
  },

  on(eventName, callback) {
    this.addListener(eventName || DEFAULT_CHANGE_EVENT, callback)
  },

  saved(data) {
    this.isSaving = false
    this.trigger(DEFAULT_SAVED_EVENT, data)
    this.trigger(DEFAULT_CHANGE_EVENT)
  },

  saving() {
    this.isSaving = true
    this.trigger(DEFAULT_CHANGE_EVENT)
    this.trigger(DEFAULT_SAVING_EVENT)
  },

  subscriptions: {},

  trigger(eventName, data) {
    this.emit(eventName || DEFAULT_CHANGE_EVENT, data)
  },
})
