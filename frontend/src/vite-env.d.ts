/// <reference types="vite/client" />

interface Window {
    __ENV__?: {
        VITE_API_URL: string;
        VITE_WS_URL: string;
    };
}

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    readonly VITE_WS_URL: string;
}
