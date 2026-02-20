import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Define the tabs available in the legacy dashboard
export type DashboardTab =
    | 'model'
    | 'voice'
    | 'transcriber'
    | 'tools'
    | 'campaigns'
    | 'connectivity'
    | 'system'
    | 'advanced'
    | 'history'
    | 'analysis'
    | 'flow'

export type ProfileId = 'browser' | 'twilio' | 'telnyx'

interface UIState {
    activeTab: DashboardTab
    activeProfile: ProfileId
    sidebarWidth: number
    showSidebar: boolean
}

// Load initial width from localStorage if available
const savedWidth = localStorage.getItem('sidebarWidth')
const initialWidth = savedWidth ? parseInt(savedWidth) : 480

const initialState: UIState = {
    activeTab: 'model',
    activeProfile: 'browser',
    sidebarWidth: initialWidth,
    showSidebar: true
}

export const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setActiveTab: (state, action: PayloadAction<DashboardTab>) => {
            state.activeTab = action.payload
        },
        setActiveProfile: (state, action: PayloadAction<ProfileId>) => {
            state.activeProfile = action.payload
        },
        setSidebarWidth: (state, action: PayloadAction<number>) => {
            state.sidebarWidth = action.payload
            localStorage.setItem('sidebarWidth', action.payload.toString())
        },
        toggleSidebar: (state) => {
            state.showSidebar = !state.showSidebar
        }
    }
})

export const { setActiveTab, setActiveProfile, setSidebarWidth, toggleSidebar } = uiSlice.actions
export default uiSlice.reducer
