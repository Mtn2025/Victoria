import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { BrowserConfig } from '@/types/config'
import { Activity, Webhook, CloudLightning } from 'lucide-react'
import { Input } from '@/components/ui/Input'

type AnalysisTab = 'prompt' | 'data' | 'webhook'

export const AnalysisSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)
    const [activeTab, setActiveTab] = useState<AnalysisTab>('prompt')

    const update = <K extends keyof BrowserConfig>(key: K, value: BrowserConfig[K]) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    const handlePrettify = () => {
        try {
            const parsed = JSON.parse(browser.extractionSchema)
            const pretty = JSON.stringify(parsed, null, 2)
            update('extractionSchema', pretty)
        } catch (e) {
            alert('Invalid JSON')
        }
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                    <Activity className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Análisis & Datos</h3>
                    <p className="text-xs text-slate-400">Post-Call Processing, Extraction & Webhooks.</p>
                </div>
            </div>

            {/* Inner Tabs */}
            <div className="bg-slate-900/50 border border-white/5 rounded-xl p-1">
                <div className="flex space-x-1 mb-4 p-1 bg-black/20 rounded-lg">
                    <button
                        onClick={() => setActiveTab('prompt')}
                        className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${activeTab === 'prompt' ? 'bg-slate-700 text-white shadow' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                        📝 Prompts & Rubric
                    </button>
                    <button
                        onClick={() => setActiveTab('data')}
                        className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${activeTab === 'data' ? 'bg-slate-700 text-white shadow' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                        💾 Extraction Data
                    </button>
                    <button
                        onClick={() => setActiveTab('webhook')}
                        className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${activeTab === 'webhook' ? 'bg-slate-700 text-white shadow' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                        📡 Webhooks
                    </button>
                </div>

                {/* 1. PROMPTS & RUBRIC */}
                {activeTab === 'prompt' && (
                    <div className="space-y-4 px-3 pb-3">
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <div className="flex justify-between items-center mb-2">
                                <h5 className="text-xs font-bold text-slate-300">Analysis Prompt</h5>
                                <span className="text-[10px] text-slate-500">Instrucciones para resumir la llamada</span>
                            </div>
                            <textarea
                                aria-label="Analysis Prompt"
                                value={browser.analysisPrompt}
                                onChange={(e) => update('analysisPrompt', e.target.value)}
                                className="w-full h-24 bg-black/30 border border-white/10 rounded p-2 text-xs font-sans text-slate-300 focus:outline-none resize-none"
                                placeholder="Resume la llamada en 3 puntos clave..."
                            />
                        </div>

                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <div className="flex justify-between items-center mb-2">
                                <h5 className="text-xs font-bold text-slate-300">Success Criteria (Rubric)</h5>
                                <span className="text-[10px] text-slate-500">Criterios para marcar Éxito/Fracaso</span>
                            </div>
                            <textarea
                                aria-label="Success Rubric"
                                value={browser.successRubric}
                                onChange={(e) => update('successRubric', e.target.value)}
                                className="w-full h-20 bg-black/30 border border-white/10 rounded p-2 text-xs font-sans text-slate-300 focus:outline-none resize-none"
                                placeholder="- Cliente aceptó agendar cita..."
                            />
                        </div>

                        {/* Toggles */}
                        <div className="flex gap-4">
                            <div className="flex-1 bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex justify-between items-center">
                                <div>
                                    <span className="text-xs font-bold text-slate-300 block">Sentiment Score</span>
                                    <span className="text-[10px] text-slate-500">Calcular sentimiento (-1 a 1)</span>
                                </div>
                                <input
                                    type="checkbox"
                                    aria-label="Sentiment Analysis"
                                    checked={browser.sentimentAnalysis}
                                    onChange={(e) => update('sentimentAnalysis', e.target.checked)}
                                    className="toggle-checkbox"
                                />
                            </div>
                            <div className="flex-1 bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex justify-between items-center">
                                <div>
                                    <span className="text-xs font-bold text-slate-300 block">Cost Tracking</span>
                                    <span className="text-[10px] text-slate-500">Estimar costo de la sesión</span>
                                </div>
                                <input
                                    type="checkbox"
                                    aria-label="Cost Tracking"
                                    checked={browser.costTrackingEnabled}
                                    onChange={(e) => update('costTrackingEnabled', e.target.checked)}
                                    className="toggle-checkbox"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* 2. DATA EXTRACTION */}
                {activeTab === 'data' && (
                    <div className="px-3 pb-3">
                        <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                            <div className="bg-slate-800 px-3 py-2 flex justify-between items-center border-b border-slate-700">
                                <span className="text-xs font-mono text-amber-400">extraction_schema.json</span>
                                <button
                                    onClick={handlePrettify}
                                    className="text-[10px] bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-white transition"
                                >
                                    Prettify
                                </button>
                            </div>
                            <div className="bg-purple-900/20 p-2 border-b border-purple-900/30">
                                <p className="text-[10px] text-purple-200/70">
                                    ⚠ Define el JSON Schema de los datos que deseas extraer de la conversación.
                                </p>
                            </div>
                            <textarea
                                aria-label="Extraction Schema"
                                value={browser.extractionSchema}
                                onChange={(e) => update('extractionSchema', e.target.value)}
                                className="w-full h-64 bg-[#0B1121] text-xs font-mono text-slate-300 p-4 focus:outline-none resize-none"
                                placeholder='{"customer_intent": "string"}'
                            />
                        </div>

                        <div className="mt-4 bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex justify-between items-center">
                            <div>
                                <span className="text-xs font-bold text-slate-300 block">PII Redaction</span>
                                <span className="text-[10px] text-slate-500">Sanitizar datos sensibles antes de guardar/enviar.</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="PII Redaction"
                                checked={browser.piiRedactionEnabled}
                                onChange={(e) => update('piiRedactionEnabled', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>
                    </div>
                )}

                {/* 3. WEBHOOKS */}
                {activeTab === 'webhook' && (
                    <div className="space-y-4 px-3 pb-3">
                        <div className="glass-panel p-5 rounded-xl border border-white/5 relative">
                            <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                                <Webhook className="w-5 h-5 text-green-500" />
                                End-of-Call Webhook
                            </h4>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Webhook URL</label>
                                    <Input
                                        aria-label="Webhook URL"
                                        value={browser.webhookUrl}
                                        onChange={(e) => update('webhookUrl', e.target.value)}
                                        placeholder="https://api.crm.com/calls/end"
                                    />
                                </div>

                                <div>
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Webhook Secret (HMAC)</label>
                                    <Input
                                        aria-label="Webhook Secret"
                                        type="password"
                                        value={browser.webhookSecret}
                                        onChange={(e) => update('webhookSecret', e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="glass-panel p-5 rounded-xl border border-white/5 relative opacity-70">
                            <h4 className="text-sm font-bold text-slate-400 mb-4 flex items-center gap-2">
                                <CloudLightning className="w-5 h-5 text-slate-500" />
                                Streaming Logs Webhook (Debug)
                            </h4>
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Log URL</label>
                                <Input
                                    aria-label="Log Webhook URL"
                                    value={browser.logWebhookUrl}
                                    onChange={(e) => update('logWebhookUrl', e.target.value)}
                                    placeholder="https://logs.monitor.com/ingest"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Data Retention (Days)</label>
                            <Input
                                aria-label="Data Retention"
                                type="number"
                                value={browser.retentionDays}
                                onChange={(e) => update('retentionDays', parseInt(e.target.value))}
                                className="text-center"
                                placeholder="30"
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
