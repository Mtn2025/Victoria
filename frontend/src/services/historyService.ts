import { api } from './api'
import { CallDetail, HistoryResponse, HistoryCall, HistoryBackendResponse } from '@/types/history'

export const historyService = {
    // Get paginated history from Real Backend
    getHistory: async (page = 1, limit = 20, filter = 'all'): Promise<HistoryResponse> => {
        const params: Record<string, any> = { page, limit }
        if (filter !== 'all') {
            params.client_type = filter
        }

        const response = await api.get<HistoryBackendResponse>('/history/rows', { params })

        // Map Backend key "duration" to Frontend key "duration_seconds" if needed
        // Backend returns: { calls: [...], total: ... }
        const mappedCalls: HistoryCall[] = response.calls.map((c) => ({
            id: c.id,
            start_time: c.start_time,
            end_time: c.end_time || null, // Backend might not send end_time yet
            client_type: c.client_type,
            status: c.status,
            duration_seconds: c.duration, // Mapping duration -> duration_seconds
            extracted_data: c.extracted_data
        }))

        return {
            calls: mappedCalls,
            total: response.total,
            page: response.page
        }
    },

    getCallDetail: async (id: string): Promise<CallDetail> => {
        return api.get<CallDetail>(`/history/${id}/detail`)
    },

    deleteCalls: async (ids: string[]): Promise<{ deleted: number }> => {
        return api.post('/history/delete-selected', { ids })
    },

    clearHistory: async (): Promise<{ deleted: number }> => {
        return api.post('/history/clear')
    }
}
