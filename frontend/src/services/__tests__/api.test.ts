import { api } from '@/services/api';
// Mock fetch globally
global.fetch = jest.fn();

describe('API Service Integration', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
    });

    it('realiza petición GET correctamente', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true, data: [] }),
            headers: new Headers(),
        });

        const response = await api.get('/test');
        expect(response).toEqual({ success: true, data: [] });
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/test'),
            expect.objectContaining({ method: 'GET' })
        );
    });

    it('maneja errores de API', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            statusText: 'Internal Server Error',
            headers: new Headers(),
        });

        await expect(api.get('/error')).rejects.toThrow('API Error: Internal Server Error');
    });
});
