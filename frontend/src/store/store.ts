import { configureStore } from '@reduxjs/toolkit'
import uiReducer from './slices/uiSlice'
import configReducer from './slices/configSlice'
import authReducer from './slices/authSlice'
import callsReducer from './slices/callsSlice'

export const store = configureStore({
    reducer: {
        ui: uiReducer,
        config: configReducer,
        auth: authReducer,
        calls: callsReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
