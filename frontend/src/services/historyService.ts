import { api } from './api'
import { CallDetail, HistoryResponse, HistoryCall, HistoryBackendResponse, CallDetailBackendResponse } from '@/types/history'

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
        const response = await api.get<CallDetailBackendResponse>(`/history/${id}/detail`)

        // Map backend fields to frontend types
        return {
            call: {
                id: response.call.id,
                start_time: response.call.start_time,
                end_time: response.call.end_time || null,
                client_type: response.call.client_type,
                status: response.call.status,
                duration_seconds: response.call.duration,  // duration -> duration_seconds
                extracted_data: response.call.extracted_data,
            },
            transcripts: response.transcripts,
        }
    },

    deleteCalls: async (ids: string[]): Promise<{ deleted: number }> => {
        return api.post('/history/delete-selected', { ids })
    },

    clearHistory: async (): Promise<{ deleted: number }> => {
        return api.post('/history/clear')
    }
}
