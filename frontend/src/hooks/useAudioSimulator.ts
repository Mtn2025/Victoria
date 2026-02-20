import { useState, useEffect, useRef, useCallback } from 'react';

export interface TranscriptMessage {
    role: 'user' | 'assistant' | 'system';
    text: string;
    timestamp: string;
}

export interface SimulatorMetrics {
    llm_latency: string | null;
    tts_latency: string | null;
}

export type SimulatorState = 'ready' | 'connecting' | 'connected' | 'error';

export interface DebugLog {
    type: string;
    event?: string;
    data?: unknown;
    timestamp: string;
    [key: string]: unknown;
}

interface UseAudioSimulatorProps {
    onTranscript?: (msg: TranscriptMessage) => void;
    onDebugLog?: (log: DebugLog) => void;
}

export const useAudioSimulator = ({ onTranscript, onDebugLog }: UseAudioSimulatorProps = {}) => {
    const [simState, setSimState] = useState<SimulatorState>('ready');
    const [vadLevel, setVadLevel] = useState(0);
    const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
    const [metrics, setMetrics] = useState<SimulatorMetrics>({ llm_latency: null, tts_latency: null });
    const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);

    const ws = useRef<WebSocket | null>(null);
    const audioContext = useRef<AudioContext | null>(null);
    const processor = useRef<AudioWorkletNode | null>(null);
    const mediaStream = useRef<MediaStream | null>(null);
    const analyser = useRef<AnalyserNode | null>(null);
    const outputAnalyser = useRef<AnalyserNode | null>(null);
    const speakingTimer = useRef<NodeJS.Timeout | null>(null);

    // Initializate Audio Context
    const initAudioContext = useCallback(async () => {
        const AudioCtor = window.AudioContext || (window as any).webkitAudioContext;
        if (!audioContext.current) {
            audioContext.current = new AudioCtor({ sampleRate: 24000 }); // Updated to 24kHz for better quality if supported
        }
        if (audioContext.current?.state === 'suspended') {
            await audioContext.current.resume();
        }
    }, []);

    const addDebugLog = useCallback((type: string, data: any) => {
        if (onDebugLog) {
            const log: DebugLog = {
                type,
                ...data,
                timestamp: new Date().toISOString().split('T')[1].slice(0, -1) // HH:mm:ss.sss
            }
            onDebugLog(log);
        }
    }, [onDebugLog]);

    // Stop Test
    const stopTest = useCallback(() => {
        console.log("Stopping simulator test...");
        setSimState('ready');
        addDebugLog('SYSTEM', { event: 'STOP_TEST' });

        if (ws.current) {
            ws.current.onclose = null;
            ws.current.close();
            ws.current = null;
        }

        if (processor.current) {
            processor.current.disconnect();
            processor.current.port.onmessage = null;
            processor.current = null;
        }

        if (mediaStream.current) {
            mediaStream.current.getTracks().forEach(t => t.stop());
            mediaStream.current = null;
        }

        if (audioContext.current) {
            audioContext.current.close().catch(console.error);
            audioContext.current = null;
        }

        analyser.current = null;
        outputAnalyser.current = null;
        setIsAgentSpeaking(false);
    }, [addDebugLog]);

    const playAudio = useCallback((base64Data: string) => {
        if (!base64Data || !audioContext.current) return;

        // TODO: This uses the PCM Worklet if available, or just fallback?
        // For now relying on worklet is best for streaming.
        // If worklet is not waiting for data, we can't push.

        if (processor.current) {
            try {
                const binaryString = window.atob(base64Data);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const pcm16 = new Int16Array(bytes.buffer);
                processor.current.port.postMessage(pcm16); // Send to worklet for playback

                setIsAgentSpeaking(true);
                if (speakingTimer.current) clearTimeout(speakingTimer.current);
                speakingTimer.current = setTimeout(() => {
                    setIsAgentSpeaking(false);
                }, 300);

            } catch (e) {
                console.error("Playback Error", e);
            }
        }
    }, []);

    // Start Test
    const startTest = useCallback(async (config: { initialMsg: string, initiator: string, voiceStyle: string }) => {
        try {
            if (simState === 'connected' || simState === 'connecting') {
                stopTest();
                return;
            }

            setSimState('connecting');
            setTranscripts([]);
            addDebugLog('SYSTEM', { event: 'START_TEST_INIT', config });

            // Note: In development using proxy, path might need adjustment.
            // Assuming /api/v1/ws/... is proxied to backend:8000/ws/...
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // Use window.location.host since frontend acts as proxy or CORS is handled
            const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/media-stream?client=browser` +
                `&initial_message=${encodeURIComponent(config.initialMsg)}` +
                `&initiator=${encodeURIComponent(config.initiator)}` +
                `&voice_style=${encodeURIComponent(config.voiceStyle)}`;

            console.log("Connecting to WS:", wsUrl);

            // Init WS
            ws.current = new WebSocket(wsUrl);
            ws.current.binaryType = 'arraybuffer';

            ws.current.onopen = async () => {
                console.log("WS Connected");
                setSimState('connected');
                addDebugLog('WS', { event: 'OPEN' });

                // Init Mic
                await initMicrophone();

                // Send Start
                if (ws.current?.readyState === WebSocket.OPEN) {
                    const startMsg = {
                        event: 'start',
                        start: {
                            streamSid: 'browser-' + Date.now(),
                            callSid: 'sim-' + Date.now(),
                            media_format: { encoding: 'audio/pcm', sample_rate: 24000, channels: 1 }
                        }
                    };
                    ws.current.send(JSON.stringify(startMsg));
                    addDebugLog('WS_SEND', { event: 'START', data: startMsg });
                }
            };

            ws.current.onmessage = (event) => {
                if (event.data instanceof ArrayBuffer) {
                    // Binary Audio (PCM16)
                    const pcm16 = new Int16Array(event.data);
                    if (processor.current) {
                        processor.current.port.postMessage(pcm16);

                        setIsAgentSpeaking(true);
                        if (speakingTimer.current) clearTimeout(speakingTimer.current);
                        speakingTimer.current = setTimeout(() => {
                            setIsAgentSpeaking(false);
                        }, 300);
                    }
                } else {
                    // Text Control Messages
                    try {
                        const msg = JSON.parse(event.data);
                        // Filter out incessant logs if needed, but for debug we want them
                        if (msg.event !== 'media' && msg.type !== 'audio') {
                            addDebugLog('WS_RECV', msg);
                        }

                        if (msg.event === 'media' || msg.type === 'audio') {
                            const payload = msg.media ? msg.media.payload : msg.data;
                            playAudio(payload);
                        } else if (msg.type === 'debug') {

                            if (msg.event === 'speech_state') setIsAgentSpeaking(msg.data.speaking);
                            else if (msg.event === 'vad_level') setVadLevel(msg.data.rms);
                            else if (msg.event === 'llm_latency') setMetrics(m => ({ ...m, llm_latency: msg.data.duration_ms + ' ms' }));
                            else if (msg.event === 'tts_latency') setMetrics(m => ({ ...m, tts_latency: msg.data.duration_ms + ' ms' }));

                        } else if (msg.type === 'transcript') {
                            const newMsg: TranscriptMessage = {
                                role: msg.role,
                                text: msg.text,
                                timestamp: new Date().toLocaleTimeString()
                            };
                            setTranscripts(prev => [...prev, newMsg]);
                            if (onTranscript) onTranscript(newMsg);
                        }
                    } catch (err) {
                        console.error("Error processing WS message:", err);
                    }
                }
            };

            ws.current.onclose = (event) => {
                console.log("WS Closed", event);
                addDebugLog('WS', { event: 'CLOSE', code: event.code, reason: event.reason });
                stopTest();
            };

            ws.current.onerror = (e) => {
                console.error("WS Error", e);
                addDebugLog('WS', { event: 'ERROR' });
                // Don't stop immediately, let close handle it or retry?
                // stopTest(); 
            };

        } catch (e) {
            console.error("Connection failed", e);
            stopTest();
        }
    }, [simState, initAudioContext, stopTest, playAudio, onTranscript, addDebugLog]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopTest();
        };
    }, [stopTest]);

    const initMicrophone = async () => {
        try {
            await initAudioContext();
            if (!audioContext.current) return;

            // Analysers
            analyser.current = audioContext.current.createAnalyser();
            analyser.current.fftSize = 512; // Higher resolution for visualizer

            outputAnalyser.current = audioContext.current.createAnalyser();
            outputAnalyser.current.fftSize = 512;
            outputAnalyser.current.connect(audioContext.current.destination);

            // Media Stream
            mediaStream.current = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 24000 // Request 24k if possible
                }
            });

            const source = audioContext.current.createMediaStreamSource(mediaStream.current);
            source.connect(analyser.current);

            // Load Worklet
            try {
                // Ensure this path is correct and accessible in public folder
                await audioContext.current.audioWorklet.addModule('/audio-worklet-processor.js');

                processor.current = new AudioWorkletNode(audioContext.current, 'pcm-processor', {
                    outputChannelCount: [1]
                });

                processor.current.port.onmessage = (event) => {
                    // Message from Worklet (Microphone Data)
                    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

                    // Expecting base64 or raw bytes? 
                    // To matching backend expectations (Twilio style base64 in JSON)
                    // The worklet should send us Int16Array
                    const pcm16 = event.data;

                    // Convert to base64
                    const bytes = new Uint8Array(pcm16.buffer);
                    let binary = '';
                    const len = bytes.byteLength;
                    // Chunking to avoid stack overflow
                    const CHUNK_SIZE = 0x8000;
                    for (let i = 0; i < len; i += CHUNK_SIZE) {
                        binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + CHUNK_SIZE)));
                    }
                    const base64Audio = window.btoa(binary);

                    ws.current.send(JSON.stringify({
                        event: 'media',
                        media: {
                            payload: base64Audio,
                            track: 'inbound',
                            timestamp: Date.now()
                        }
                    }));
                };

                source.connect(processor.current);
                processor.current.connect(outputAnalyser.current!);

                addDebugLog('AUDIO', { event: 'WORKLET_LOADED' });

            } catch (err) {
                console.error("AudioWorklet Error", err);
                addDebugLog('AUDIO', { event: 'WORKLET_ERROR', error: String(err) });
                alert("Audio Worklet Error. Ensure /audio-worklet-processor.js exists in public/");
            }

        } catch (e) {
            console.error("Mic Error", e);
            addDebugLog('AUDIO', { event: 'MIC_ERROR', error: String(e) });
            stopTest();
        }
    };

    return {
        simState,
        vadLevel,
        isAgentSpeaking,
        metrics,
        transcripts,
        analyser: analyser.current,
        outputAnalyser: outputAnalyser.current,
        startTest,
        stopTest
    };
};
