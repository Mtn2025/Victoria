import { useState, useCallback } from 'react';
import { useAudioSimulator, DebugLog } from '@/hooks/useAudioSimulator';
import { AudioVisualizer } from '@/components/features/Simulator/AudioVisualizer';
import { ChatInterface } from '@/components/features/Simulator/ChatInterface';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Terminal, ChevronDown, ChevronUp } from 'lucide-react';

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
                    <Button
                        variant="ghost"
                        size="sm"
                        className={`text-slate-400 hover:text-white ${showDebug ? 'bg-slate-800' : ''}`}
                        onClick={() => setShowDebug(!showDebug)}
                        title="Toggle Debug Console"
                    >
                        <Terminal size={14} />
                    </Button>
                    <div className="w-px h-4 bg-slate-700" />

                    <Input
                        data-testid="input-sim-phone"
                        placeholder="Mensaje inicial..."
                        value={config.initialMsg}
                        onChange={(e) => setConfig(prev => ({ ...prev, initialMsg: e.target.value }))}
                        className="w-64 h-8 text-xs"
                    />

                    <select
                        data-testid="select-sim-visualizer"
                        className="bg-slate-800 text-xs text-white border border-slate-600 rounded px-2 h-8"
                        value={visualizerMode}
                        onChange={(e) => setVisualizerMode(e.target.value as 'wave' | 'bars' | 'orb')}
                    >
                        <option value="wave">Onda</option>
                        <option value="bars">Barras</option>
                        <option value="orb">Orbe</option>
                    </select>

                    <Button
                        data-testid="btn-start-sim"
                        onClick={handleStart}
                        variant={simState === 'connected' ? 'danger' : 'primary'}
                        className="h-8"
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
                        {/* Metrics Overlay */}
                        {simState === 'connected' && (
                            <div className="absolute top-4 left-4 z-20 flex flex-col space-y-2 pointer-events-none">
                                <div className="flex items-center space-x-2 bg-black/40 p-1 rounded backdrop-blur-sm">
                                    <span className={`w-2 h-2 rounded-full transition-all ${vadLevel > 0.05 ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-slate-600'}`} />
                                    <span className="text-[10px] font-mono text-slate-400">MIC INPUT ({vadLevel.toFixed(3)})</span>
                                </div>
                                <div className="flex items-center space-x-2 bg-black/40 p-1 rounded backdrop-blur-sm">
                                    <span className={`w-2 h-2 rounded-full transition-all ${isAgentSpeaking ? 'bg-blue-500 shadow-[0_0_10px_#3b82f6]' : 'bg-slate-600'}`} />
                                    <span className="text-[10px] font-mono text-slate-400">AGENT TTS</span>
                                </div>
                                <div className="text-[10px] font-mono text-slate-500 mt-2">
                                    <div>LLM: {metrics.llm_latency || '-'}</div>
                                    <div>TTS: {metrics.tts_latency || '-'}</div>
                                </div>
                            </div>
                        )}

                        {/* Status Overlay */}
                        {simState !== 'connected' && (
                            <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
                                <p className={`font-mono text-emerald-500/50 text-xl ${simState === 'connecting' ? 'animate-pulse' : ''}`}>
                                    {simState === 'connecting' ? 'Estableciendo Conexión...' : 'Listo para conectar...'}
                                </p>
                            </div>
                        )}

                        <AudioVisualizer
                            mode={visualizerMode}
                            analyser={analyser}
                            outputAnalyser={outputAnalyser}
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
