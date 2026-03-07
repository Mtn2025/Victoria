// Basic wrapper around fetch
import { ApiError } from '@/utils/ApiError';
export const api = {
    get: async <T>(url: string, config: any = {}): Promise<T> => {
        return request<T>('GET', url, undefined, config)
    },

    post: async <T>(url: string, body: any = {}, config: any = {}): Promise<T> => {
        return request<T>('POST', url, body, config)
    },

    put: async <T>(url: string, body: any = {}, config: any = {}): Promise<T> => {
        return request<T>('PUT', url, body, config)
    },

    patch: async <T>(url: string, body: any = {}, config: any = {}): Promise<T> => {
        return request<T>('PATCH', url, body, config)
    },

    /**
     * postForm — Sends multipart/form-data (FileUpload + fields).
     * Do NOT set Content-Type header — browser sets it automatically with the correct boundary.
     */
    postForm: async <T>(url: string, formData: FormData): Promise<T> => {
        const apiKey = localStorage.getItem('api_key')
        const headers: Record<string, string> = {
            ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        }
        const fullUrl = '/api' + url
        const response = await fetch(fullUrl, {
            method: 'POST',
            headers,
            body: formData,
        })
        if (!response.ok) {
            let errorData
            try { errorData = await response.json() } catch { errorData = null }
            const { ApiError } = await import('@/utils/ApiError')
            throw new ApiError(`API Error: ${response.statusText}`, response.status, response.statusText, errorData)
        }
        return response.json()
    },

    delete: async <T>(url: string, config: any = {}): Promise<T> => {
        return request<T>('DELETE', url, undefined, config)
    }
}

async function request<T>(method: string, url: string, body?: any, config: any = {}): Promise<T> {
    // Read API key from localStorage — stored by LoginPage as 'api_key'
    const apiKey = localStorage.getItem('api_key')

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        ...config.headers,
    }

    const query = config.params ? '?' + new URLSearchParams(config.params).toString() : ''
    const fullUrl = '/api' + url + query

    const response = await fetch(fullUrl, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    })



    // ... inside request function ...
    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = null;
        }
        throw new ApiError(`API Error: ${response.statusText}`, response.status, response.statusText, errorData);
    }

    if (config.responseType === 'blob') {
        return response.blob() as unknown as T
    }

    return response.json()
}
