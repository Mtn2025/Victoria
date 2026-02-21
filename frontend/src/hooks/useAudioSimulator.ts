import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_BASE_URL } from '../utils/constants';

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

    // Keep a ref to the latest onDebugLog so that logging functions can
    // read it without being listed as a dependency (which would cascade into
    // stopTest/startTest recreations and trigger useEffect cleanup on re-renders).
    const onDebugLogRef = useRef(onDebugLog);
    useEffect(() => { onDebugLogRef.current = onDebugLog; }, [onDebugLog]);

    const addDebugLog = useCallback((type: string, data: any) => {
        if (onDebugLogRef.current) {
            const log: DebugLog = {
                type,
                ...data,
                timestamp: new Date().toISOString().split('T')[1].slice(0, -1)
            };
            onDebugLogRef.current(log);
        }
    }, []); // stable — reads onDebugLog via ref

    // stopTest is intentionally defined with EMPTY deps [] so its identity is
    // stable across ALL re-renders. It reads onDebugLog via onDebugLogRef,
    // and setState dispatchers (setSimState, setIsAgentSpeaking) are guaranteed
    // stable by React. All other targets are refs.
    //
    // WHY: If stopTest had any non-ref dependency (e.g. addDebugLog), it would
    // re-create on every render that changes that dep. The component receives
    // the new stopTest, and useEffect(cleanup, [stopTest]) fires its cleanup,
    // calling stopTest() and closing the WebSocket mid-session.
    const stopTest = useCallback(() => {
        console.warn('[DIAG] stopTest() CALLED FROM:', new Error().stack);
        console.log('Stopping simulator test...');
        setSimState('ready');
        // Inline the debug log using the ref directly (not addDebugLog) to
        // avoid any closure or dependency issue.
        if (onDebugLogRef.current) {
            onDebugLogRef.current({
                type: 'SYSTEM',
                event: 'STOP_TEST',
                timestamp: new Date().toISOString().split('T')[1].slice(0, -1)
            });
        }

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
    }, []); // stable — all reads go through refs or stable dispatchers

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

            // Note: WS_BASE_URL is injected by Nginx/envsubst or Vite fallback 
            // e.g. wss://api.victoria.com/ws/media-stream
            // agent_id = active agent UUID from Redux (empty → backend falls back to active agent)
            const { store } = await import('../store/store')
            const agentUuid = store.getState().agents.activeAgent?.agent_uuid ?? ''
            const wsUrl = `${WS_BASE_URL}?client=browser` +
                (agentUuid ? `&agent_id=${encodeURIComponent(agentUuid)}` : '') +
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
                    console.log('[DIAG] AUDIO RECEIVED', event.data.byteLength, 'bytes | processor.current:', processor.current);
                    const pcm16 = new Int16Array(event.data);
                    if (processor.current) {
                        processor.current.port.postMessage(pcm16);

                        setIsAgentSpeaking(true);
                        if (speakingTimer.current) clearTimeout(speakingTimer.current);
                        speakingTimer.current = setTimeout(() => {
                            setIsAgentSpeaking(false);
                        }, 300);
                    } else {
                        console.warn('[DIAG] AUDIO DROPPED — processor.current is null (worklet not ready yet)');
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
                // DIAG: log all WS close details
                console.warn('[DIAG] WS CLOSED | code:', event.code, '| reason:', event.reason || '(none)', '| wasClean:', event.wasClean);
                addDebugLog('WS', { event: 'CLOSE', code: event.code, reason: event.reason, wasClean: event.wasClean });
                stopTest();
            };

            ws.current.onerror = (e) => {
                // DIAG: log WS error details
                console.error('[DIAG] WS ERROR event:', e);
                addDebugLog('WS', { event: 'ERROR', detail: String(e) });
                // onerror is always followed by onclose — stopTest() runs there
            };

        } catch (e) {
            console.error('Connection failed', e);
            stopTest();
        }
    }, [simState, initAudioContext, stopTest, playAudio, onTranscript, addDebugLog]);

    // Cleanup on true unmount only.
    // deps = [] is correct: stopTest is now identity-stable (empty deps useCallback),
    // so React will not re-run this effect on re-renders.
    useEffect(() => {
        return () => { stopTest(); };
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
                    sampleRate: 24000
                }
            });

            // CRITICAL: Resume AudioContext *after* getUserMedia.
            // Browsers suspend the AudioContext if it was created before a user
            // gesture (or resume it lazily). getUserMedia provides the right
            // moment to ensure the context is running before we wire the graph.
            if (audioContext.current.state === 'suspended') {
                await audioContext.current.resume();
                console.log('[DIAG] AudioContext resumed after getUserMedia, state:', audioContext.current.state);
            } else {
                console.log('[DIAG] AudioContext state after getUserMedia:', audioContext.current.state);
            }

            const source = audioContext.current.createMediaStreamSource(mediaStream.current);
            source.connect(analyser.current);

            // Load Worklet
            try {
                await audioContext.current.audioWorklet.addModule('/audio-worklet-processor.js');

                processor.current = new AudioWorkletNode(audioContext.current, 'pcm-processor', {
                    numberOfInputs: 1,    // standard: request one input bus so mic data flows in
                    numberOfOutputs: 1,
                    outputChannelCount: [1],
                    channelCount: 1,
                    channelCountMode: 'explicit',
                } as AudioWorkletNodeOptions);

                processor.current.port.onmessage = (event) => {
                    // Microphone chunk from AudioWorklet → encode → send to backend
                    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

                    const pcm16 = event.data as Int16Array;
                    // Skip debug-type messages from worklet
                    if (!pcm16 || !(pcm16 instanceof Int16Array)) return;

                    const bytes = new Uint8Array(pcm16.buffer);
                    let binary = '';
                    const len = bytes.byteLength;
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

                console.log('[DIAG] WORKLET_LOADED, AudioContext state:', audioContext.current.state);
                addDebugLog('AUDIO', { event: 'WORKLET_LOADED' });

            } catch (err) {
                // AudioWorklet failed (e.g. path not found, browser unsupported).
                // DO NOT close the WS — the session must stay open so the user can
                // still hear the greeting. Mic output just won't be sent.
                console.error('AudioWorklet Error', err);
                addDebugLog('AUDIO', { event: 'WORKLET_ERROR', error: String(err) });
                // Note: no alert() here — it blocks the browser thread and destabilises WS state.
            }

        } catch (e) {
            // getUserMedia failed (permission denied, no device, non-HTTPS, etc.).
            // DO NOT call stopTest() — that would close the WebSocket and disconnect
            // the backend session. The session stays open; the user just can't send audio.
            // The backend greeting will still play.
            console.error('Mic Error', e);
            addDebugLog('AUDIO', { event: 'MIC_ERROR', error: String(e) });
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
