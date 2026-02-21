import { configureStore } from '@reduxjs/toolkit'
import uiReducer from './slices/uiSlice'
import configReducer from './slices/configSlice'
import agentsReducer from './slices/agentsSlice'

// Auth: X-API-Key in localStorage. No JWT flow — authSlice/useAuth/callsSlice removed as dead code.
export const store = configureStore({
    reducer: {
        ui: uiReducer,
        config: configReducer,
        agents: agentsReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
