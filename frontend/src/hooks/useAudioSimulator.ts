/**
 * useAudioSimulator — Ref-first architecture.
 *
 * DESIGN RULES:
 *   1. All mutable state lives in useRef — never causes re-renders.
 *   2. React state (useState) is only for UI rendering: simState, isAgentSpeaking, transcripts.
 *   3. startTest and stopTest are stored in refs so they never change identity.
 *      No useCallback, no cross-dependencies.
 *   4. useEffect cleanup has deps=[] — fires ONLY on true unmount, never on re-renders.
 *   5. Callbacks passed as props (onTranscript, onDebugLog) are kept in refs so they
 *      can be read with the latest value without being listed as dependencies.
 */
import { useState, useEffect, useRef } from 'react';
import { WS_BASE_URL } from '../utils/constants';

// ─── Types ───────────────────────────────────────────────────────────────────

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

// ─── Hook ────────────────────────────────────────────────────────────────────

export const useAudioSimulator = ({ onTranscript, onDebugLog }: UseAudioSimulatorProps = {}) => {

    // ── UI state (only for rendering) ──
    const [simState, setSimState] = useState<SimulatorState>('ready');
    const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
    const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);
    const [vadLevel, setVadLevel] = useState(0);
    const [metrics, setMetrics] = useState<SimulatorMetrics>({ llm_latency: null, tts_latency: null });

    // ── Mutable refs (never trigger re-renders) ──
    const ws = useRef<WebSocket | null>(null);
    const audioCtx = useRef<AudioContext | null>(null);
    const processor = useRef<AudioWorkletNode | null>(null);
    const stream = useRef<MediaStream | null>(null);
    const analyser = useRef<AnalyserNode | null>(null);
    const outputAnalyser = useRef<AnalyserNode | null>(null);
    const speakingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    // ── Prop refs (always up-to-date without dep lists) ──
    const onTranscriptRef = useRef(onTranscript);
    const onDebugLogRef = useRef(onDebugLog);
    useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);
    useEffect(() => { onDebugLogRef.current = onDebugLog; }, [onDebugLog]);

    // ─────────────────────────────────────────────────────────────────────────
    // Helpers (plain functions — zero React deps)
    // ─────────────────────────────────────────────────────────────────────────

    const log = (type: string, data: Record<string, unknown> = {}) => {
        if (!onDebugLogRef.current) return;
        onDebugLogRef.current({
            type,
            ...data,
            timestamp: new Date().toISOString().split('T')[1].slice(0, -1),
        });
    };

    const markAgentSpeaking = () => {
        setIsAgentSpeaking(true);
        if (speakingTimer.current) clearTimeout(speakingTimer.current);
        speakingTimer.current = setTimeout(() => setIsAgentSpeaking(false), 300);
    };

    // Feed raw PCM16 bytes to the AudioWorklet for playback.
    const feedAudioToWorklet = (pcm16: Int16Array) => {
        if (!processor.current) {
            console.warn('[SIM] feedAudioToWorklet: processor not ready, dropping frame');
            return;
        }
        processor.current.port.postMessage(pcm16);
        markAgentSpeaking();
    };

    // Decode base64 TTS payload (JSON media event) → PCM16 → worklet.
    const playBase64Audio = (base64Data: string) => {
        if (!base64Data || !audioCtx.current) return;
        try {
            const binary = window.atob(base64Data);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
            feedAudioToWorklet(new Int16Array(bytes.buffer));
        } catch (e) {
            console.error('[SIM] playBase64Audio error:', e);
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // stopTest — stored in a ref so its identity is permanently stable.
    // The component can call stopTestFn.current() directly.
    // ─────────────────────────────────────────────────────────────────────────

    const stopTestFn = useRef<() => void>(() => { });
    stopTestFn.current = () => {
        console.warn('[DIAG] stopTest() CALLED FROM:', new Error().stack);

        // Null out onclose FIRST to prevent re-entrant stopTest call from onclose handler.
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
        if (stream.current) {
            stream.current.getTracks().forEach(t => t.stop());
            stream.current = null;
        }
        if (audioCtx.current) {
            audioCtx.current.close().catch(() => { });
            audioCtx.current = null;
        }
        if (speakingTimer.current) {
            clearTimeout(speakingTimer.current);
            speakingTimer.current = null;
        }
        analyser.current = null;
        outputAnalyser.current = null;

        setSimState('ready');
        setIsAgentSpeaking(false);
        log('SYSTEM', { event: 'STOP_TEST' });
    };

    // ─────────────────────────────────────────────────────────────────────────
    // initMicrophone — plain async function, no deps.
    // ─────────────────────────────────────────────────────────────────────────

    const initMicrophone = async () => {
        try {
            // ── 1. AudioContext ──
            if (!audioCtx.current) {
                const AC = window.AudioContext || (window as any).webkitAudioContext;
                audioCtx.current = new AC({ sampleRate: 24000 });
            }

            // ── 2. getUserMedia ──
            stream.current = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 24000,
                },
            });

            // ── 3. Resume context AFTER getUserMedia (browser gesture unlock) ──
            if (audioCtx.current.state === 'suspended') {
                await audioCtx.current.resume();
            }
            console.log('[DIAG] AudioContext state after getUserMedia:', audioCtx.current.state);

            // ── 4. Build analyser nodes ──
            analyser.current = audioCtx.current.createAnalyser();
            analyser.current.fftSize = 512;

            outputAnalyser.current = audioCtx.current.createAnalyser();
            outputAnalyser.current.fftSize = 512;
            outputAnalyser.current.connect(audioCtx.current.destination);

            // ── 5. Wire mic source to analyser ──
            const source = audioCtx.current.createMediaStreamSource(stream.current);
            source.connect(analyser.current);

            // ── 6. Load AudioWorklet ──
            try {
                await audioCtx.current.audioWorklet.addModule('/audio-worklet-processor.js');

                processor.current = new AudioWorkletNode(audioCtx.current, 'pcm-processor', {
                    numberOfInputs: 1,
                    numberOfOutputs: 1,
                    outputChannelCount: [1],
                    channelCount: 1,
                    channelCountMode: 'explicit',
                } as AudioWorkletNodeOptions);

                // Worklet → hook: mic data chunks (Int16Array) sent to backend.
                processor.current.port.onmessage = (ev) => {
                    const data = ev.data;

                    // Debug message from worklet (e.g. empty_input)
                    if (data && typeof data === 'object' && data.type === 'debug') {
                        console.warn('[WORKLET]', data.msg, 'count:', data.count);
                        return;
                    }

                    // Mic PCM16 chunk — encode as base64 and send to backend.
                    if (!(data instanceof Int16Array)) return;
                    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

                    const bytes = new Uint8Array(data.buffer);
                    let binary = '';
                    for (let i = 0; i < bytes.byteLength; i++) {
                        binary += String.fromCharCode(bytes[i]);
                    }
                    const b64 = window.btoa(binary);
                    console.log('[MIC CHUNK SENT]', bytes.byteLength, 'bytes');

                    ws.current.send(JSON.stringify({
                        event: 'media',
                        media: { payload: b64, track: 'inbound', timestamp: Date.now() },
                    }));
                };

                // Wire: mic source → worklet → output analyser → speakers.
                source.connect(processor.current);
                processor.current.connect(outputAnalyser.current);

                console.log('[DIAG] WORKLET_LOADED, AudioContext state:', audioCtx.current.state);
                log('AUDIO', { event: 'WORKLET_LOADED' });

            } catch (err) {
                // Worklet failure: keep WS open — user still hears greeting.
                console.error('[SIM] AudioWorklet load failed:', err);
                log('AUDIO', { event: 'WORKLET_ERROR', error: String(err) });
            }

        } catch (err) {
            // getUserMedia failure: keep WS open — greeting still plays.
            console.error('[SIM] getUserMedia failed:', err);
            log('AUDIO', { event: 'MIC_ERROR', error: String(err) });
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // startTest — stored in a ref so its identity is permanently stable.
    // ─────────────────────────────────────────────────────────────────────────

    const startTestFn = useRef<(config: { initialMsg: string; initiator: string; voiceStyle: string }) => Promise<void>>(
        async () => { }
    );
    startTestFn.current = async (config) => {
        // Guard: if already running, stop first.
        if (ws.current) {
            stopTestFn.current();
            return;
        }

        setSimState('connecting');
        setTranscripts([]);
        log('SYSTEM', { event: 'START_TEST_INIT', config });

        try {
            // Resolve active agent UUID from Redux store (dynamic import avoids circular dep).
            const { store } = await import('../store/store');
            const agentUuid = store.getState().agents.activeAgent?.agent_uuid ?? '';

            const wsUrl =
                `${WS_BASE_URL}?client=browser` +
                (agentUuid ? `&agent_id=${encodeURIComponent(agentUuid)}` : '') +
                `&initial_message=${encodeURIComponent(config.initialMsg)}` +
                `&initiator=${encodeURIComponent(config.initiator)}` +
                `&voice_style=${encodeURIComponent(config.voiceStyle)}`;

            console.log('[SIM] Connecting to WS:', wsUrl);
            const socket = new WebSocket(wsUrl);
            socket.binaryType = 'arraybuffer';
            ws.current = socket;

            // ── onopen ──
            socket.onopen = async () => {
                console.log('[SIM] WS connected');
                setSimState('connected');
                log('WS', { event: 'OPEN' });

                // Init mic (non-fatal — WS stays open even if mic fails).
                await initMicrophone();

                // Send start event to backend.
                if (socket.readyState === WebSocket.OPEN) {
                    const startMsg = {
                        event: 'start',
                        start: {
                            streamSid: 'browser-' + Date.now(),
                            callSid: 'sim-' + Date.now(),
                            media_format: { encoding: 'audio/pcm', sample_rate: 24000, channels: 1 },
                        },
                    };
                    socket.send(JSON.stringify(startMsg));
                    log('WS_SEND', { event: 'START', data: startMsg });
                }
            };

            // ── onmessage ──
            socket.onmessage = (ev) => {
                // ── Binary: raw PCM16 greeting / TTS audio ──
                if (ev.data instanceof ArrayBuffer) {
                    console.log('[DIAG] AUDIO RECEIVED', ev.data.byteLength, 'bytes | processor:', processor.current);
                    feedAudioToWorklet(new Int16Array(ev.data));
                    console.log('[GREETING DONE] WS state:', ws.current?.readyState, 'processor:', !!processor.current);
                    return;
                }

                // ── Text: JSON control messages ──
                try {
                    const msg = JSON.parse(ev.data as string);

                    // Suppress media/audio spam from debug panel
                    if (msg.event !== 'media' && msg.type !== 'audio') {
                        log('WS_RECV', msg);
                    }

                    if (msg.event === 'media' || msg.type === 'audio') {
                        const payload = msg.media?.payload ?? msg.data;
                        playBase64Audio(payload);

                    } else if (msg.type === 'debug') {
                        if (msg.event === 'speech_state') setIsAgentSpeaking(msg.data?.speaking ?? false);
                        else if (msg.event === 'vad_level') setVadLevel(msg.data?.rms ?? 0);
                        else if (msg.event === 'llm_latency') setMetrics(m => ({ ...m, llm_latency: `${msg.data?.duration_ms} ms` }));
                        else if (msg.event === 'tts_latency') setMetrics(m => ({ ...m, tts_latency: `${msg.data?.duration_ms} ms` }));

                    } else if (msg.type === 'clear') {
                        console.log(`[SIM] Barge-in detected! Clearing frontend audio playback queue. Reason: ${msg.reason}`);
                        if (processor.current) {
                            processor.current.port.postMessage({ type: 'clear' });
                        }
                    } else if (msg.type === 'transcript') {
                        const newMsg: TranscriptMessage = {
                            role: msg.role,
                            text: msg.text,
                            timestamp: new Date().toLocaleTimeString(),
                        };
                        setTranscripts(prev => [...prev, newMsg]);
                        onTranscriptRef.current?.(newMsg);
                    }
                } catch (err) {
                    console.error('[SIM] onmessage parse error:', err);
                }
            };

            // ── onclose ──
            socket.onclose = (ev) => {
                console.warn('[WS CLOSE]', ev.code, ev.reason, ev.wasClean, new Date().toISOString());
                console.warn('[DIAG] WS CLOSED | code:', ev.code, '| reason:', ev.reason || '(none)', '| wasClean:', ev.wasClean);
                log('WS', { event: 'CLOSE', code: ev.code, reason: ev.reason, wasClean: ev.wasClean });
                stopTestFn.current();
            };

            // ── onerror ──
            socket.onerror = (ev) => {
                console.error('[DIAG] WS ERROR:', ev);
                log('WS', { event: 'ERROR' });
                // onclose always fires after onerror — cleanup runs there.
            };

        } catch (err) {
            console.error('[SIM] startTest failed:', err);
            stopTestFn.current();
        }
    };

    // ─────────────────────────────────────────────────────────────────────────
    // Cleanup on true unmount only — deps=[] guarantees this.
    // ─────────────────────────────────────────────────────────────────────────
    useEffect(() => {
        return () => { stopTestFn.current(); };
    }, []); // ← intentional empty deps — only run on unmount

    // ─────────────────────────────────────────────────────────────────────────
    // Public API — stable references (wrappers over refs)
    // ─────────────────────────────────────────────────────────────────────────
    return {
        simState,
        vadLevel,
        isAgentSpeaking,
        metrics,
        transcripts,
        // Expose nodes as refs so consumers can read .current without re-renders
        analyser: analyser,
        outputAnalyser: outputAnalyser,
        // Stable wrappers — identity never changes across renders
        startTest: (config: { initialMsg: string; initiator: string; voiceStyle: string }) =>
            startTestFn.current(config),
        stopTest: () => stopTestFn.current(),
    };
};
