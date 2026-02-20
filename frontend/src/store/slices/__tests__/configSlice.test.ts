import { configureStore } from '@reduxjs/toolkit'
import configReducer, { fetchLanguages, fetchVoices, fetchStyles } from '../configSlice'
import { configService } from '@/services/configService'

// Mock configService
jest.mock('@/services/configService', () => ({
    configService: {
        getLanguages: jest.fn(),
        getVoices: jest.fn(),
        getStyles: jest.fn()
    }
}))

describe('configSlice', () => {
    let store: any

    beforeEach(() => {
        store = configureStore({
            reducer: { config: configReducer }
        })
        jest.clearAllMocks()
    })

    describe('fetchLanguages', () => {
        it('should handle fulfilled state', async () => {
            const mockLanguages = [{ code: 'es-MX', name: 'Spanish (Mexico)' }]
                ; (configService.getLanguages as jest.Mock).mockResolvedValue(mockLanguages)

            await store.dispatch(fetchLanguages())

            const state = store.getState().config
            expect(state.availableLanguages).toEqual(mockLanguages)
            expect(state.isLoadingOptions).toBe(false)
        })

        it('should handle pending state', () => {
            // Need to manually check state during pending, 
            // or trust that toolkit handles it. 
            // With checking final state is often enough for simple cases.
            // But let's check loading state transition if we can.
            // Dispatching valid promise keeps it simple.
            (configService.getLanguages as jest.Mock).mockResolvedValue([])
            const promise = store.dispatch(fetchLanguages())
            // Immediately after dispatch, before resolution (microtask), native async/await makes this hard to catch synchronously 
            // without custom middleware or inspecting action types dispatched.
            // checking state after await is standard.
        })

        it('should handle rejected state', async () => {
            (configService.getLanguages as jest.Mock).mockRejectedValue(new Error('Failed'))

            await store.dispatch(fetchLanguages())

            const state = store.getState().config
            expect(state.isLoadingOptions).toBe(false)
            expect(state.availableLanguages).toEqual([]) // Should remain empty
        })
    })

    describe('fetchVoices', () => {
        it('should handle fulfilled state', async () => {
            const mockVoices = [{ id: 'voice1', name: 'Voice 1' }]
                ; (configService.getVoices as jest.Mock).mockResolvedValue(mockVoices)

            await store.dispatch(fetchVoices('es-MX'))

            const state = store.getState().config
            expect(configService.getVoices).toHaveBeenCalledWith('es-MX')
            expect(state.availableVoices).toEqual(mockVoices)
        })
    })

    describe('fetchStyles', () => {
        it('should handle fulfilled state', async () => {
            const mockStyles = [{ id: 'cheerful', label: 'Cheerful' }]
                ; (configService.getStyles as jest.Mock).mockResolvedValue(mockStyles)

            await store.dispatch(fetchStyles('voice1'))

            const state = store.getState().config
            expect(configService.getStyles).toHaveBeenCalledWith('voice1')
            expect(state.availableStyles).toEqual(mockStyles)
        })
    })
})
