import { useState, useCallback } from 'react';
import { useAudioSimulator, DebugLog } from '@/hooks/useAudioSimulator';
import { AudioVisualizer } from '@/components/features/Simulator/AudioVisualizer';
import { ChatInterface } from '@/components/features/Simulator/ChatInterface';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Terminal } from 'lucide-react';

const SimulatorPage = () => {
    const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);
    const [showDebug, setShowDebug] = useState(false);

    const handleDebugLog = useCallback((log: DebugLog) => {
        setDebugLogs(prev => [log, ...prev].slice(0, 100)); // Keep last 100
    }, []);

    const {
        simState,
        vadLevel,
        isAgentSpeaking,
        metrics,
        transcripts,
        analyser,
        outputAnalyser,
        startTest,
        stopTest
    } = useAudioSimulator({ onDebugLog: handleDebugLog });

    const [visualizerMode, setVisualizerMode] = useState<'wave' | 'bars' | 'orb'>('wave');
    const [config, setConfig] = useState({
        initialMsg: '',
        voiceStyle: '',
        initiator: 'speak-first'
    });

    const handleStart = () => {
        if (simState === 'connected' || simState === 'connecting') {
            stopTest();
        } else {
            startTest(config);
        }
    };

    return (
        <div className="p-4 h-[calc(100vh-64px)] flex flex-col space-y-4">
            {/* Header / Controls */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-3">
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span>🧪</span> Simulador 2.0
                    </h1>
                </div>

                <div className="flex items-center space-x-4 bg-slate-900/50 p-2 rounded-lg border border-slate-700">
                    <div className="group relative flex items-center">
                        <Button
                            variant="ghost"
                            size="icon"
                            className={`text-slate-400 hover:text-white transition-colors flex-shrink-0 ${showDebug ? 'bg-slate-800 text-blue-400' : ''}`}
                            onClick={() => setShowDebug(!showDebug)}
                            title="Consola de Depuración (Logs de red, webSockets y latencias)"
                        >
                            <Terminal size={18} />
                        </Button>
                        {/* Tooltip on hover */}
                        <div className="absolute right-0 top-full mt-2 w-48 p-2 bg-slate-800 text-[10px] text-slate-300 rounded shadow-xl border border-slate-700 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                            <strong>Panel Debug:</strong> Permite visualizar los mensajes crudos del WebSocket y métricas de latencia de IA.
                        </div>
                    </div>
                    <div className="flex flex-col relative group">
                        <Input
                            data-testid="input-sim-phone"
                            placeholder="Mensaje inicial (Opcional)..."
                            value={config.initialMsg}
                            onChange={(e) => setConfig(prev => ({ ...prev, initialMsg: e.target.value }))}
                            className="w-64 text-sm"
                        />
                        {/* Helper text invisible by default, visible on hover */}
                        <span className="absolute top-11 left-0 w-max text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 px-2 py-1 rounded border border-slate-700 pointer-events-none z-50 shadow-lg">
                            Ej: "Hola, soy Juan". Forzará al agente a responder a este saludo al conectar.
                        </span>
                    </div>

                    <select
                        data-testid="select-sim-visualizer"
                        className="bg-slate-800 text-sm font-medium text-white border border-slate-600 outline-none focus:border-blue-500 rounded-lg px-3 py-2 cursor-pointer transition-colors hover:bg-slate-700"
                        value={visualizerMode}
                        onChange={(e) => setVisualizerMode(e.target.value as 'wave' | 'bars' | 'orb')}
                        title="Estilo de animación visual"
                    >
                        <option value="wave">Onda</option>
                        <option value="bars">Barras</option>
                        <option value="orb">Orbe</option>
                    </select>

                    <Button
                        data-testid="btn-start-sim"
                        onClick={handleStart}
                        variant={simState === 'connected' ? 'danger' : 'primary'}
                        size="md"
                        className="w-40 font-bold"
                    >
                        {simState === 'connected' ? '⏹ Detener' : (simState === 'connecting' ? '⏳ Conectando...' : '▶ Iniciar Prueba')}
                    </Button>
                </div>
            </div>

            {/* Main Content Split */}
            <div className="flex-1 min-h-0 flex flex-col space-y-4">

                {/* Visualizer Area */}
                <div className="flex-1 relative bg-black rounded-xl border border-slate-800 overflow-hidden shadow-inner flex">
                    {/* Visualizer Canvas */}
                    <div className={`relative h-full transition-all duration-300 ${showDebug ? 'w-2/3 border-r border-slate-800' : 'w-full'}`}>
                        {/* Metrics Overlay (Indicators, NOT buttons) */}
                        {simState === 'connected' && (
                            <div className="absolute top-4 left-4 z-20 flex flex-col space-y-3 pointer-events-none bg-black/60 backdrop-blur-md p-3 rounded-xl border border-white/10 shadow-xl">
                                <span className="text-[9px] uppercase tracking-widest text-slate-500 font-bold mb-1">Telemetría de Red</span>
                                <div className="flex items-center space-x-3">
                                    <div className={`relative flex items-center justify-center w-5 h-5 rounded-full border ${vadLevel > 0.05 ? 'border-green-500 bg-green-500/20' : 'border-slate-700 bg-slate-800'}`}>
                                        <span className={`w-2 h-2 rounded-full transition-all ${vadLevel > 0.05 ? 'bg-green-400 shadow-[0_0_8px_#4ade80]' : 'bg-slate-600'}`} />
                                    </div>
                                    <span className="text-[11px] font-mono text-slate-300">USER MIC <span className="opacity-50 inline-block w-8 text-right">({vadLevel.toFixed(2)})</span></span>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className={`relative flex items-center justify-center w-5 h-5 rounded-full border ${isAgentSpeaking ? 'border-blue-500 bg-blue-500/20' : 'border-slate-700 bg-slate-800'}`}>
                                        <span className={`w-2 h-2 rounded-full transition-all ${isAgentSpeaking ? 'bg-blue-400 shadow-[0_0_8px_#60a5fa]' : 'bg-slate-600'}`} />
                                    </div>
                                    <span className="text-[11px] font-mono text-slate-300">AGENT TTS</span>
                                </div>
                                <div className="h-px w-full bg-slate-800 my-1" />
                                <div className="flex flex-col space-y-1">
                                    <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 w-full gap-4">
                                        <span>LLM Latency:</span> <span className="text-emerald-400 font-bold">{metrics.llm_latency || '--'}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 w-full gap-4">
                                        <span>TTS Latency:</span> <span className="text-emerald-400 font-bold">{metrics.tts_latency || '--'}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Status Overlay Profesional */}
                        {simState !== 'connected' && (
                            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none bg-slate-950/40 backdrop-blur-[2px]">
                                <div className="flex flex-col items-center space-y-4 p-6 rounded-2xl bg-black/60 border border-white/5 shadow-2xl backdrop-blur-md">
                                    {simState === 'connecting' ? (
                                        <>
                                            <div className="w-12 h-12 rounded-full border-t-2 border-r-2 border-blue-500 animate-spin" />
                                            <h3 className="text-blue-400 font-medium tracking-wide animate-pulse">Estableciendo Conexión Segura...</h3>
                                        </>
                                    ) : (
                                        <>
                                            <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-2 shadow-inner border border-slate-700/50">
                                                <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center animate-pulse">
                                                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                                </div>
                                            </div>
                                            <h3 className="text-slate-200 font-semibold text-lg tracking-wide">Sistema en Reposo</h3>
                                            <p className="text-slate-500 text-sm">Haz clic en "Iniciar Prueba" para conectar con el agente interactivo.</p>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}

                        <AudioVisualizer
                            mode={visualizerMode}
                            analyser={analyser.current}
                            outputAnalyser={outputAnalyser.current}
                            isAgentSpeaking={isAgentSpeaking}
                        />
                    </div>

                    {/* Debug Panel (Slide in) */}
                    {showDebug && (
                        <div className="w-1/3 bg-slate-900 overflow-hidden flex flex-col">
                            <div className="p-2 border-b border-slate-800 text-xs font-bold text-slate-400 uppercase tracking-wider flex justify-between">
                                <span>Console Logs</span>
                                <button onClick={() => setDebugLogs([])} className="hover:text-white">Clear</button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-2 font-mono text-[10px] space-y-1 custom-scrollbar">
                                {debugLogs.map((log, i) => (
                                    <div key={i} className="break-all border-b border-slate-800/50 pb-1 mb-1">
                                        <div className="flex gap-2 text-slate-500">
                                            <span>{log.timestamp}</span>
                                            <span className={`font-bold ${log.type === 'WS_SEND' ? 'text-blue-400' :
                                                log.type === 'WS_RECV' ? 'text-green-400' :
                                                    log.type === 'ERROR' ? 'text-red-400' :
                                                        'text-slate-300'
                                                }`}>{log.type}</span>
                                        </div>
                                        <div className="text-slate-400 pl-4">
                                            {JSON.stringify(log, (k, v) => k === 'type' || k === 'timestamp' ? undefined : v)}
                                        </div>
                                    </div>
                                ))}
                                {debugLogs.length === 0 && (
                                    <div className="text-slate-600 italic text-center mt-4">No logs yet...</div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Transcripts (Fixed Height) */}
                <div className="h-64 shrink-0">
                    <ChatInterface transcripts={transcripts} />
                </div>

            </div>
        </div>
    );
};

export default SimulatorPage;
