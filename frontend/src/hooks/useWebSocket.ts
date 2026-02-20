import { useEffect, useRef, useCallback } from 'react';
import { useDispatch } from 'react-redux';
// import { addWebhookCall } from '../store/slices/callsSlice';

export const useWebSocket = (url: string) => {
    const ws = useRef<WebSocket | null>(null);
    const dispatch = useDispatch();

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return;

        ws.current = new WebSocket(url);

        ws.current.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // Dispatch actions based on message type
                // if (data.type === 'call_update') {
                //     dispatch(addWebhookCall(data.payload));
                // }
                console.log('WS Message:', data);
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };

        ws.current.onclose = () => {
            console.log('WebSocket disconnected, retrying in 3s...');
            setTimeout(connect, 3000);
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

    }, [url, dispatch]);

    useEffect(() => {
        connect();
        return () => {
            ws.current?.close();
        };
    }, [connect]);

    const sendMessage = (msg: any) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(msg));
        } else {
            console.warn('WebSocket not connected');
        }
    };

    return { sendMessage };
};
