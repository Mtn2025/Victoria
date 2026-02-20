import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { BrowserConfig } from '@/types/config'
import { Disc, Clock, Voicemail } from 'lucide-react'
import { Input } from '@/components/ui/Input'

export const FlowSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)

    const update = <K extends keyof BrowserConfig>(key: K, value: BrowserConfig[K]) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    // Helper to safely parse/stringify JSON array strings if backend stores them as strings?
    // Assuming backend config keeps them as strings based on legacy HTML placeholder usage, 
    // but Typescript types might define them as string[]. Let's assume string for input binding for now
    // If config state has array, we join.
    // The legacy placeholder='["para", ...]' suggests it might be a JSON string or an array processed.
    // For simplicity, we bind directly assuming current config structure supports it.

    // Actually, looking at legacy html: input type="text" x-model="c.interruptionPhrases". 
    // This implies c.interruptionPhrases is a string in the alpine component.
    // We should treat it as string in UI for manual edit of JSON array.

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* 1. Interrupciones (Barge-in) */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Disc className="w-24 h-24 text-rose-500" />
                </div>

                <div className="flex justify-between items-center mb-6 relative z-10">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                            Interrupciones (Barge-in)
                        </h3>
                        <p className="text-xs text-slate-400 mt-1">Controla cuándo y cómo el usuario puede interrumpir al bot.</p>
                    </div>
                    <input
                        type="checkbox"
                        aria-label="Barge-in Logic"
                        checked={browser.bargeInEnabled}
                        onChange={(e) => update('bargeInEnabled', e.target.checked)}
                        className="toggle-checkbox"
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sensibilidad</label>
                            <span className="text-xs font-mono text-rose-400">
                                {browser.interruptionSensitivity} ({browser.interruptionSensitivity > 0.8 ? 'Alta' : 'Baja'})
                            </span>
                        </div>
                        <input
                            type="range"
                            aria-label="Interruption Sensitivity"
                            min="0" max="1" step="0.1"
                            value={browser.interruptionSensitivity}
                            onChange={(e) => update('interruptionSensitivity', parseFloat(e.target.value))}
                            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-rose-500"
                        />
                        <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                            <span>Difícil</span>
                            <span>Fácil</span>
                        </div>
                    </div>

                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Frases de Ruptura (Force Stop)</label>
                            <span className="text-[10px] text-slate-500">JSON Array</span>
                        </div>
                        <Input
                            aria-label="Interruption Phrases"
                            value={browser.interruptionPhrases}
                            onChange={(e) => update('interruptionPhrases', e.target.value)}
                            placeholder='["para", "espera", "escúchame"]'
                        />
                    </div>
                </div>
            </div>

            {/* 2. Buzón de Voz (Voicemail) */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Voicemail className="w-24 h-24 text-amber-500" />
                </div>

                <div className="flex justify-between items-center mb-6 relative z-10">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                            Detección de Buzón (AMD)
                        </h3>
                        <p className="text-xs text-slate-400 mt-1">Detectar contestadoras automáticas y dejar mensaje.</p>
                    </div>
                    <input
                        type="checkbox"
                        aria-label="Voicemail Detection"
                        checked={browser.voicemailDetectionEnabled}
                        onChange={(e) => update('voicemailDetectionEnabled', e.target.checked)}
                        className="toggle-checkbox"
                    />
                </div>

                <div className="grid grid-cols-1 gap-6 relative z-10">
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Mensaje para Buzón</label>
                        <textarea
                            aria-label="Voicemail Message"
                            value={browser.voicemailMessage}
                            onChange={(e) => update('voicemailMessage', e.target.value)}
                            className="glass-input w-full p-3 rounded-lg text-sm bg-slate-900/50 text-slate-200 border border-slate-700 focus:outline-none focus:border-amber-500 transition-colors"
                            rows={2}
                            placeholder="Hola, llamaba de Ubrokers..."
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Sensibilidad AMD</label>
                            <Input
                                type="number"
                                aria-label="AMD Sensitivity"
                                step="0.1" min="0" max="1"
                                value={browser.machineDetectionSensitivity}
                                onChange={(e) => update('machineDetectionSensitivity', parseFloat(e.target.value))}
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Acción</label>
                            <select className="glass-input w-full p-2.5 rounded-lg text-sm opacity-50 cursor-not-allowed bg-slate-800 text-slate-400 border border-slate-700" disabled>
                                <option>Dejar Mensaje y Colgar</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* 3. Ritmo y Naturalidad (Pacing) */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Clock className="w-24 h-24 text-emerald-500" />
                </div>

                <div className="flex justify-between items-center mb-6 relative z-10">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                            Ritmo y Naturalidad
                        </h3>
                        <p className="text-xs text-slate-400 mt-1">Ajuste fino de tiempos y respuesta humana.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Latencia Artificial</label>
                            <span className="text-xs font-mono text-emerald-400">{browser.responseDelaySeconds}s</span>
                        </div>
                        <input
                            type="range"
                            aria-label="Response Delay"
                            min="0" max="3" step="0.1"
                            value={browser.responseDelaySeconds}
                            onChange={(e) => update('responseDelaySeconds', parseFloat(e.target.value))}
                            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                        />
                        <p className="text-[10px] text-slate-500 mt-2">Simula tiempo de "pensamiento" antes de responder.</p>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-300">Esperar Saludo ("Hola")</span>
                            <input
                                type="checkbox"
                                aria-label="Wait for Greeting"
                                checked={browser.waitForGreeting}
                                onChange={(e) => update('waitForGreeting', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-300">Hyphenation (Fluidez)</span>
                            <input
                                type="checkbox"
                                aria-label="Hyphenation Enabled"
                                checked={browser.hyphenationEnabled}
                                onChange={(e) => update('hyphenationEnabled', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>
                    </div>

                    <div className="col-span-1 md:col-span-2">
                        <div className="flex justify-between mb-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Frases de Despedida (Auto-Hangup)</label>
                            <span className="text-[10px] text-slate-500">JSON Array</span>
                        </div>
                        <Input
                            aria-label="End Call Phrases"
                            value={browser.endCallPhrases}
                            onChange={(e) => update('endCallPhrases', e.target.value)}
                            placeholder='["gracias", "adiós", "hasta luego"]'
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
