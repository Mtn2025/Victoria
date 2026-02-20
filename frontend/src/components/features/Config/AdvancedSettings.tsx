import { useState, useEffect } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { BrowserConfig } from '@/types/config'
import { Sliders, Zap, MessageSquare, Activity } from 'lucide-react'

export const AdvancedSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)

    // Local state for "Patience" slider logic (maps to silenceTimeoutMs)
    // 0.2s to 3.0s
    const [patience, setPatience] = useState(browser.sttSilenceTimeout / 1000)

    useEffect(() => {
        setPatience(browser.sttSilenceTimeout / 1000)
    }, [browser.sttSilenceTimeout])

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    const handlePatienceChange = (val: number) => {
        setPatience(val)
        update('sttSilenceTimeout', Math.round(val * 1000))
    }

    const getPatienceLabel = (val: number) => {
        if (val < 0.5) return 'Rápido (Interuptivo)'
        if (val > 1.5) return 'Muy Paciente'
        return 'Balanceado'
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-indigo-500/10 rounded-lg">
                    <Sliders className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Calidad y Latencia</h3>
                    <p className="text-xs text-slate-400">Ajuste fino del motor de voz y tiempos de respuesta.</p>
                </div>
            </div>

            {/* 1. Paciencia (Silence Timeout) */}
            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50 relative overflow-hidden group hover:border-indigo-500/30 transition-all">
                <div className="flex justify-between items-center mb-4">
                    <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Paciencia del Asistente
                    </label>
                    <span className="text-xs bg-slate-900 text-indigo-400 px-2 py-1 rounded border border-indigo-500/20">
                        {getPatienceLabel(patience)}
                    </span>
                </div>

                <div className="relative h-12 flex items-center">
                    {/* Visual Tracks */}
                    <div className="absolute w-full h-2 bg-slate-700 rounded-lg"></div>
                    <div className="absolute left-0 w-1/3 h-2 bg-gradient-to-r from-red-500/20 to-yellow-500/20 rounded-l-lg"></div>
                    <div className="absolute right-0 w-1/3 h-2 bg-gradient-to-l from-green-500/20 to-yellow-500/20 rounded-r-lg"></div>

                    <input
                        type="range"
                        aria-label="Paciencia del Asistente"
                        min="0.2" max="3.0" step="0.1"
                        value={patience}
                        onChange={(e) => handlePatienceChange(parseFloat(e.target.value))}
                        className="w-full h-2 bg-transparent appearance-none cursor-pointer relative z-10 accent-indigo-500"
                    />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                    <span>⚡ Rápido (200ms)</span>
                    <span>🐢 Paciente (3s)</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-2 italic">
                    Define cuánto silencio espera Andrea antes de responder.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 2. Supresion de Ruido */}
                <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-emerald-400" />
                        Supresión de Ruido
                    </h4>
                    <div className="space-y-3">
                        <label className="block text-xs text-slate-500 mb-1">Nivel Krisp AI</label>
                        <div className="grid grid-cols-3 gap-2">
                            {['off', 'balanced', 'high'].map(level => (
                                <button
                                    key={level}
                                    aria-label={`Noise Suppression ${level}`}
                                    onClick={() => update('noiseSuppressionLevel', level)}
                                    className={`px-2 py-2 rounded text-xs font-bold border transition-all uppercase ${browser.noiseSuppressionLevel === level
                                        ? level === 'balanced' ? 'bg-emerald-600 text-white border-emerald-500' :
                                            level === 'high' ? 'bg-indigo-600 text-white border-indigo-500' :
                                                'bg-slate-600 text-white border-slate-500'
                                        : 'bg-slate-900 text-slate-500 border-slate-800'
                                        }`}
                                >
                                    {level}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 3. Calidad de Audio */}
                <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-400" />
                        Fidelidad de Audio
                    </h4>
                    <div className="space-y-3">
                        <label className="block text-xs text-slate-500 mb-1">Codec & Sample Rate</label>
                        <Select
                            aria-label="Codec Selection"
                            value={browser.audioCodec}
                            onChange={(e) => update('audioCodec', e.target.value)}
                        >
                            <option value="PCMU">G.711 PCMU (8kHz)</option>
                            <option value="PCMA">G.711 PCMA (8kHz)</option>
                            <option value="OPUS">Opus (Alta Fidelidad)</option>
                        </Select>
                        <p className="text-[10px] text-slate-500 mt-1">Usa PCMU para llamadas PSTN normales.</p>
                    </div>
                </div>
            </div>

            {/* 4. Escucha Activa */}
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-pink-500/10 rounded-full">
                        <MessageSquare className="w-5 h-5 text-pink-400" />
                    </div>
                    <div>
                        <h4 className="text-sm font-bold text-white">Escucha Activa (Backchanneling)</h4>
                        <p className="text-xs text-slate-400">Permite decir "Ajá", "Entiendo" mientras hablas.</p>
                    </div>
                </div>
                <input
                    type="checkbox"
                    aria-label="Backchannel Toggle"
                    checked={browser.enableBackchannel}
                    onChange={(e) => update('enableBackchannel', e.target.checked)}
                    className="toggle-checkbox"
                />
            </div>

            {/* Safety Limits */}
            <div className="pt-4 border-t border-slate-700">
                <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Límites de Seguridad</h4>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs uppercase text-slate-500 block mb-1">Duración Máx (Seg)</label>
                        <Input
                            type="number"
                            aria-label="Max Duration"
                            value={browser.maxDuration}
                            onChange={(e) => update('maxDuration', parseInt(e.target.value))}
                        />
                    </div>
                    <div>
                        <label className="text-xs uppercase text-slate-500 block mb-1">Max Retries</label>
                        <Input
                            type="number"
                            aria-label="Max Retries"
                            value={browser.maxRetries}
                            onChange={(e) => update('maxRetries', parseInt(e.target.value))}
                        />
                    </div>
                    <div className="col-span-2">
                        <label className="text-xs uppercase text-slate-500 block mb-1">Mensaje Inactividad</label>
                        <Input
                            aria-label="Idle Message"
                            value={browser.idleMessage}
                            onChange={(e) => update('idleMessage', e.target.value)}
                            placeholder="¿Hola? ¿Sigues ahí?"
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
