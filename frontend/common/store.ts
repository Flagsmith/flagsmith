import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'
import {
  FLUSH,
  PAUSE,
  PERSIST,
  persistReducer,
  persistStore,
  PURGE,
  REGISTER,
  REHYDRATE,
} from 'redux-persist'
import storage from 'redux-persist/lib/storage'
import { Persistor } from 'redux-persist/es/types'
import { service } from './service'
import selectedOrganisationReducer from './selectedOrganisationSlice'
// END OF IMPORTS
const createStore = () => {
  const reducer = combineReducers({
    [service.reducerPath]: service.reducer,
    selectedOrganisation: selectedOrganisationReducer,
    // END OF REDUCERS
  })

  return configureStore({
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(service.middleware),
    // END OF MIDDLEWARE
    // @ts-ignore typescript is confused by the turnary
    reducer: persistReducer(
      {
        key: 'root',
        storage,
        version: 1,
        whitelist: ['user'],
      },
      reducer,
    ),
  })
}

type StoreType = ReturnType<typeof createStore>
let _store: StoreType
let _persistor: Persistor
export const getPersistor = () => _persistor
export const getStore = function (): StoreType {
  if (_store) return _store
  _store = createStore()
  _persistor = persistStore(_store)
  setupListeners(_store.dispatch)
  return _store
}

export type StoreStateType = ReturnType<StoreType['getState']>
