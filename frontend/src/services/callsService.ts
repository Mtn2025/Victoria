import { api } from './api';
import { Call, CallFilter } from '../types/call';
import { ApiResponse } from '../types/api';

const BASE_URL = '/calls';

export const callsService = {
    getAll: async (filter?: CallFilter): Promise<ApiResponse<Call[]>> => {
        return api.get(BASE_URL, { params: filter });
    },

    getById: async (id: string): Promise<ApiResponse<Call>> => {
        return api.get(`${BASE_URL}/${id}`);
    },

    initiateCall: async (to: string, from: string): Promise<ApiResponse<Call>> => {
        return api.post(BASE_URL, { to, from });
    },

    terminateCall: async (id: string): Promise<ApiResponse<void>> => {
        return api.post(`${BASE_URL}/${id}/terminate`);
    },

    deleteCalls: async (ids: string[]): Promise<ApiResponse<void>> => {
        return api.post(`${BASE_URL}/delete-batch`, { ids });
    },

    // Legacy compatibility if needed, or new endpoint
    getHistory: async (page: number, limit: number, filter?: CallFilter): Promise<ApiResponse<{ items: Call[], total: number }>> => {
        return api.get(BASE_URL, { params: { page, limit, ...filter } });
    }
};
