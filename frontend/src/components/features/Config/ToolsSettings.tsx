import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Wrench, Globe, Code } from 'lucide-react'

export const ToolsSettings = () => {
    const dispatch = useAppDispatch()
    const { browser, twilio, telnyx } = useAppSelector(state => state.config)
    const [targetProfile, setTargetProfile] = useState<'browser' | 'twilio' | 'telnyx'>('browser')
    const [subTab, setSubTab] = useState<'schema' | 'server' | 'security'>('schema')

    // Helper to get current config object based on targetProfile
    const getConfig = () => {
        switch (targetProfile) {
            case 'twilio': return twilio;
            case 'telnyx': return telnyx;
            default: return browser;
        }
    }

    const config = getConfig()

    // Helper to update
    const update = (key: string, value: any) => {
        if (targetProfile === 'browser') dispatch(updateBrowserConfig({ [key]: value } as any))
        if (targetProfile === 'twilio') dispatch(updateTwilioConfigState({ [key]: value } as any))
        if (targetProfile === 'telnyx') dispatch(updateTelnyxConfigState({ [key]: value } as any))
    }

    const handlePrettify = () => {
        try {
            const parsed = JSON.parse(config.toolsSchema)
            const pretty = JSON.stringify(parsed, null, 2)
            update('toolsSchema', pretty)
        } catch (e) {
            alert('Invalid JSON')
        }
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-amber-500/10 rounded-lg">
                        <Wrench className="w-5 h-5 text-amber-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">Herramientas & Acciones</h3>
                        <p className="text-xs text-slate-400">Function Calling, n8n Webhooks y Client Tools.</p>
                    </div>
                </div>

                {/* Profile Selector */}
                <select
                    aria-label="Profile Selector"
                    value={targetProfile}
                    onChange={(e) => setTargetProfile(e.target.value as any)}
                    className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-xs text-white"
                >
                    <option value="browser">Browser</option>
                    <option value="twilio">Twilio</option>
                    <option value="telnyx">Telnyx</option>
                </select>
            </div>

            {/* Sub-Tabs */}
            <div className="bg-slate-900/50 border border-white/5 rounded-xl p-1 flex space-x-1">
                {[
                    { id: 'schema', label: '📜 JSON Schema' },
                    { id: 'server', label: '🌍 Server (n8n)' },
                    { id: 'security', label: '🔒 Security' }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setSubTab(tab.id as any)}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${subTab === tab.id
                            ? 'bg-slate-700 text-white shadow'
                            : 'text-slate-500 hover:text-slate-300'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* 1. JSON Schema */}
            {subTab === 'schema' && (
                <div className="space-y-4">
                    <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                        <div className="bg-slate-800 px-3 py-2 flex justify-between items-center border-b border-slate-700">
                            <span className="text-xs font-mono text-amber-400">tools_schema.json</span>
                            <button
                                onClick={handlePrettify}
                                className="text-[10px] bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-white transition"
                            >
                                Prettify
                            </button>
                        </div>
                        <div className="bg-amber-900/20 p-2 border-b border-amber-900/30">
                            <p className="text-[10px] text-amber-200/70">
                                ⚠ Define el array de herramientas compatible con OpenAI Function Calling format.
                            </p>
                        </div>
                        <textarea
                            aria-label="JSON Schema Editor"
                            value={config.toolsSchema}
                            onChange={(e) => update('toolsSchema', e.target.value)}
                            className="w-full h-64 bg-[#0B1121] text-xs font-mono text-slate-300 p-4 focus:outline-none resize-none"
                            placeholder='[{ "type": "function", ... }]'
                        />
                    </div>

                    <div className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                        <div>
                            <span className="text-xs font-bold text-slate-300 block">Async Execution (No Blocking)</span>
                            <span className="text-[10px] text-slate-500">El audio libera mientras la herramienta se ejecuta.</span>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="Async Execution Toggle"
                            checked={config.asyncTools}
                            onChange={(e) => update('asyncTools', e.target.checked)}
                            className="toggle-checkbox"
                        />
                    </div>
                </div>
            )}

            {/* 2. Server (n8n) */}
            {subTab === 'server' && (
                <div className="space-y-4">
                    <div className="p-5 rounded-xl border border-white/5 bg-slate-900/50 relative">
                        <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                            <Globe className="w-5 h-5 text-pink-500" />
                            n8n / API Webhook
                        </h4>
                        <div className="space-y-4">
                            <Input
                                aria-label="Server URL"
                                label="Server URL (Endpoint)"
                                value={config.toolServerUrl}
                                onChange={(e) => update('toolServerUrl', e.target.value)}
                                placeholder="https://primary.n8n.com/webhook/..."
                                className="font-mono text-xs border-l-4 border-l-pink-500"
                            />
                            <Input
                                aria-label="Server Secret"
                                type="password"
                                label="Server Secret (Authorization Header)"
                                value={config.toolServerSecret}
                                onChange={(e) => update('toolServerSecret', e.target.value)}
                                placeholder="Bearer sk-..."
                                className="font-mono text-xs"
                            />
                            <div className="grid grid-cols-2 gap-4">
                                <Input
                                    aria-label="Timeout"
                                    type="number"
                                    label="Timeout (ms)"
                                    value={config.toolTimeoutMs}
                                    onChange={(e) => update('toolTimeoutMs', parseInt(e.target.value))}
                                    className="font-mono text-xs text-center"
                                />
                                <div>
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Retry On Error</label>
                                    <Select
                                        aria-label="Retry Count"
                                        value={config.toolRetryCount}
                                        onChange={(e) => update('toolRetryCount', parseInt(e.target.value))}
                                    >
                                        <option value={0}>Disabled</option>
                                        <option value={1}>1 Retry</option>
                                    </Select>
                                </div>
                            </div>
                            <Input
                                aria-label="Error Message"
                                label="Error Message (User Facing)"
                                value={config.toolErrorMsg}
                                onChange={(e) => update('toolErrorMsg', e.target.value)}
                                className="text-xs italic text-red-300 border-red-900/30"
                            />
                        </div>
                    </div>

                    <div className="bg-blue-900/10 p-4 rounded-lg border border-blue-500/20 flex justify-between items-center">
                        <div>
                            <h5 className="text-xs font-bold text-blue-300">Client Tools (Browser JS)</h5>
                            <p className="text-[10px] text-blue-400/60">Permite ejecutar funciones JS locales (popup, alert, nav).</p>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="Client Tools Toggle"
                            checked={config.clientToolsEnabled}
                            onChange={(e) => update('clientToolsEnabled', e.target.checked)}
                            className="toggle-checkbox"
                        />
                    </div>
                </div>
            )}

            {/* 3. Security */}
            {subTab === 'security' && (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-2">Parameter Redaction</h5>
                            <p className="text-[10px] text-slate-500 mb-2">Keys to mask in logs (comma separated)</p>
                            <textarea
                                aria-label="Parameter Redaction"
                                value={config.redactParams}
                                onChange={(e) => update('redactParams', e.target.value)}
                                className="w-full h-20 bg-black/30 border border-white/10 rounded p-2 text-xs font-mono focus:outline-none"
                                placeholder='["password", "credit_card", "ssn"]'
                            />
                        </div>
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-2">Transfer Whitelist</h5>
                            <p className="text-[10px] text-slate-500 mb-2">Allowed transfer numbers (comma separated)</p>
                            <textarea
                                aria-label="Transfer Whitelist"
                                value={config.transferWhitelist}
                                onChange={(e) => update('transferWhitelist', e.target.value)}
                                className="w-full h-20 bg-black/30 border border-white/10 rounded p-2 text-xs font-mono focus:outline-none"
                                placeholder='["+15550123", "+15550124"]'
                            />
                        </div>
                    </div>

                    <div className="p-3 bg-indigo-900/20 rounded border border-indigo-500/20 flex gap-3 items-center">
                        <div className="p-2 bg-indigo-500/20 rounded-full">
                            <Code className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div>
                            <span className="text-xs font-bold text-indigo-300 block">State Injection</span>
                            <span className="text-[10px] text-slate-400">Permite a las herramientas modificar el contexto global.</span>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="State Injection Toggle"
                            checked={config.stateInjectionEnabled}
                            onChange={(e) => update('stateInjectionEnabled', e.target.checked)}
                            className="ml-auto toggle-checkbox"
                        />
                    </div>
                </div>
            )}
        </div>
    )
}
