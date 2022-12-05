import { combineReducers, configureStore } from '@reduxjs/toolkit'
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
import { Persistor } from 'redux-persist/es/types'
import { service } from './service'
// END OF IMPORTS
const createStore = () => {
    const storage = require('redux-persist/lib/storage').default

    const reducer = combineReducers({
        [service.reducerPath]: service.reducer,
        // END OF REDUCERS
    })

    return configureStore({
        middleware: (getDefaultMiddleware) =>
            getDefaultMiddleware({
                serializableCheck: {
                    ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
                },
            })
                .concat(service.middleware),
                // END OF MIDDLEWARE
        // @ts-ignore typescript is confused by the turnary
        reducer:
            persistReducer(
                {
                    key: 'root',
                    storage,
                    version: 1,
                    whitelist: ['user'],
                },
                reducer,
            )
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
    return _store
}

export type StoreStateType = ReturnType<StoreType['getState']>
