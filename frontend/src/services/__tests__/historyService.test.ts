import { historyService } from '../historyService'
import { api } from '../api'

// Mock api
jest.mock('../api', () => ({
    api: {
        get: jest.fn(),
        post: jest.fn()
    }
}))

describe('historyService', () => {
    afterEach(() => {
        jest.clearAllMocks()
    })

    it('getHistory calls api.get with correct params and transforms response', async () => {
        const mockBackendResponse = {
            calls: [
                {
                    id: '1',
                    start_time: '2023-01-01T00:00:00Z',
                    end_time: '2023-01-01T00:01:00Z',
                    client_type: 'browser',
                    status: 'completed',
                    duration: 60,
                    extracted_data: { sentiment: 'positive' }
                }
            ],
            total: 100,
            page: 1
        };

        (api.get as jest.Mock).mockResolvedValue(mockBackendResponse)

        const result = await historyService.getHistory(1, 10, 'browser')

        expect(api.get).toHaveBeenCalledWith('/history/rows', {
            params: { page: 1, limit: 10, client_type: 'browser' }
        })

        expect(result.calls[0]).toEqual({
            id: '1',
            start_time: '2023-01-01T00:00:00Z',
            end_time: '2023-01-01T00:01:00Z',
            client_type: 'browser',
            status: 'completed',
            duration_seconds: 60,
            extracted_data: { sentiment: 'positive' }
        })
        expect(result.total).toBe(100)
    })

    it('getHistory handles default params', async () => {
        (api.get as jest.Mock).mockResolvedValue({ calls: [], total: 0, page: 1 })

        await historyService.getHistory()

        expect(api.get).toHaveBeenCalledWith('/history/rows', {
            params: { page: 1, limit: 20 }
        })
    })

    it('deleteCalls calls api.post', async () => {
        (api.post as jest.Mock).mockResolvedValue({ deleted: 5 })

        const ids = ['1', '2']
        const result = await historyService.deleteCalls(ids)

        expect(api.post).toHaveBeenCalledWith('/history/delete-selected', { ids })
        expect(result).toEqual({ deleted: 5 })
    })
})
