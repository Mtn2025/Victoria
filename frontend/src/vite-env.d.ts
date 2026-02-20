/// <reference types="vite/client" />

interface Window {
    __ENV__?: {
        VITE_API_URL: string;
        VITE_WS_URL: string;
    };
}
