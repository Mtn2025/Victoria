import { configureStore } from '@reduxjs/toolkit'
import callsReducer, { fetchCalls } from '../callsSlice'
import { callsService } from '@/services/callsService'

// Mock callsService
jest.mock('@/services/callsService', () => ({
    callsService: {
        getAll: jest.fn()
    }
}))

describe('callsSlice', () => {
    let store: any

    beforeEach(() => {
        store = configureStore({
            reducer: { calls: callsReducer }
        })
        jest.clearAllMocks()
    })

    describe('fetchCalls', () => {
        it('should handle fulfilled state', async () => {
            const mockCalls = [{ id: '1', status: 'completed' }]
                ; (callsService.getAll as jest.Mock).mockResolvedValue({ data: mockCalls })

            await store.dispatch(fetchCalls(undefined))

            const state = store.getState().calls
            expect(state.items).toEqual(mockCalls)
            expect(state.status).toBe('succeeded')
            expect(state.error).toBeNull()
        })

        it('should handle rejected state', async () => {
            (callsService.getAll as jest.Mock).mockRejectedValue(new Error('Network error'))

            await store.dispatch(fetchCalls(undefined))

            const state = store.getState().calls
            expect(state.status).toBe('failed')
            expect(state.error).toBe('Network error')
        })
    })
})
