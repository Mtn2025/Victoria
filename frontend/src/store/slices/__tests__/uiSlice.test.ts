import uiReducer, { setActiveTab, setActiveProfile, setSidebarWidth, toggleSidebar } from '../uiSlice'

describe('uiSlice', () => {
    const initialState = {
        activeTab: 'model' as const,
        activeProfile: 'browser' as const,
        sidebarWidth: 480,
        showSidebar: true
    }

    it('should handle initial state', () => {
        expect(uiReducer(undefined, { type: 'unknown' })).toEqual(initialState)
    })

    it('should handle setActiveTab', () => {
        const actual = uiReducer(initialState, setActiveTab('voice'))
        expect(actual.activeTab).toEqual('voice')
    })

    it('should handle setActiveProfile', () => {
        const actual = uiReducer(initialState, setActiveProfile('twilio'))
        expect(actual.activeProfile).toEqual('twilio')
    })

    it('should handle setSidebarWidth', () => {
        const actual = uiReducer(initialState, setSidebarWidth(500))
        expect(actual.sidebarWidth).toEqual(500)
    })

    it('should handle toggleSidebar', () => {
        const actual = uiReducer(initialState, toggleSidebar())
        expect(actual.showSidebar).toEqual(false)

        const actual2 = uiReducer(actual, toggleSidebar())
        expect(actual2.showSidebar).toEqual(true)
    })
})
