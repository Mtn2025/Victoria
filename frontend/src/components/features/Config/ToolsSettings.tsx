import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Accordion } from '@/components/ui/Accordion'
import { Globe, Code, FileJson, Lock } from 'lucide-react'

export const ToolsSettings = () => {
    const dispatch = useAppDispatch()

    // Obtenemos el profile activo del store general (ya no usamos estado local)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser, twilio, telnyx } = useAppSelector(state => state.config)

    // Controlamos el acordeón abierto (por defecto el Servidor n8n)
    const [openSection, setOpenSection] = useState<string | null>('server')

    // Helper para heredar valores basados en el perfil actual
    const getConfig = () => {
        switch (activeProfile) {
            case 'twilio': return twilio;
            case 'telnyx': return telnyx;
            default: return browser;
        }
    }

    const config = getConfig()

    const update = (key: string, value: any) => {
        if (activeProfile === 'browser') dispatch(updateBrowserConfig({ [key]: value } as any))
        if (activeProfile === 'twilio') dispatch(updateTwilioConfigState({ [key]: value } as any))
        if (activeProfile === 'telnyx') dispatch(updateTelnyxConfigState({ [key]: value } as any))
    }

    const handlePrettify = () => {
        try {
            const parsed = JSON.parse(config.toolsSchema)
            const pretty = JSON.stringify(parsed, null, 2)
            update('toolsSchema', pretty)
        } catch (e) {
            alert('JSON Inválido. Revisa la sintaxis.')
        }
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* 1. Server (n8n / Webhook) */}
            <Accordion
                isOpen={openSection === 'server'}
                onToggle={() => setOpenSection(openSection === 'server' ? null : 'server')}
                className="border-pink-500/30"
                headerClassName="hover:bg-pink-900/20"
                title={
                    <span className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        Conexión al Servidor (n8n / Webhook)
                    </span>
                }
            >
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
                                <option value={0}>Deshabilitado</option>
                                <option value={1}>1 Reintento</option>
                                <option value={2}>2 Reintentos</option>
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
            </Accordion>

            {/* 2. JSON Schema & Client Tools */}
            <Accordion
                isOpen={openSection === 'schema'}
                onToggle={() => setOpenSection(openSection === 'schema' ? null : 'schema')}
                className="border-amber-500/30"
                headerClassName="hover:bg-amber-900/20"
                title={
                    <span className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                        <FileJson className="w-4 h-4" />
                        JSON Schema & Client Tools
                    </span>
                }
            >
                <div className="space-y-4">
                    <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                        <div className="bg-slate-800 px-3 py-2 flex justify-between items-center border-b border-slate-700">
                            <span className="text-xs font-mono text-amber-400">tools_schema.json</span>
                            <button
                                onClick={handlePrettify}
                                className="text-[10px] bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-white transition font-medium"
                            >
                                Prettify Formato
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
                            className="w-full h-64 bg-[#0B1121] text-xs font-mono text-slate-300 p-4 focus:outline-none resize-none custom-scrollbar"
                            placeholder='[{ "type": "function", ... }]'
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                            <div>
                                <span className="text-xs font-bold text-slate-300 block">Async Execution (No Blocking)</span>
                                <span className="text-[10px] text-slate-500">Libera audio mientras se ejecuta la tool.</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Async Execution Toggle"
                                checked={config.asyncTools}
                                onChange={(e) => update('asyncTools', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>

                        <div className="flex items-center justify-between bg-blue-900/10 p-3 rounded-lg border border-blue-500/20">
                            <div>
                                <span className="text-xs font-bold text-blue-300 block">Client Tools (Browser JS)</span>
                                <span className="text-[10px] text-blue-400/60">Permite funciones JS locales (Simulador).</span>
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
                </div>
            </Accordion>

            {/* 3. Security */}
            <Accordion
                isOpen={openSection === 'security'}
                onToggle={() => setOpenSection(openSection === 'security' ? null : 'security')}
                className="border-slate-500/30"
                headerClassName="hover:bg-slate-900/20"
                title={
                    <span className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        Seguridad y Privacidad
                    </span>
                }
            >
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-2">Parameter Redaction</h5>
                            <p className="text-[10px] text-slate-500 mb-2">Llaves para enmascarar en logs (Array CSV)</p>
                            <textarea
                                aria-label="Parameter Redaction"
                                value={config.redactParams}
                                onChange={(e) => update('redactParams', e.target.value)}
                                className="w-full h-20 bg-black/30 border border-white/10 rounded p-2 text-xs font-mono focus:outline-none custom-scrollbar"
                                placeholder='["password", "credit_card", "ssn"]'
                            />
                        </div>
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-2">Transfer Whitelist</h5>
                            <p className="text-[10px] text-slate-500 mb-2">Números tolerados de desvío (Array CSV)</p>
                            <textarea
                                aria-label="Transfer Whitelist"
                                value={config.transferWhitelist}
                                onChange={(e) => update('transferWhitelist', e.target.value)}
                                className="w-full h-20 bg-black/30 border border-white/10 rounded p-2 text-xs font-mono focus:outline-none custom-scrollbar"
                                placeholder='["+15550123", "+15550124"]'
                            />
                        </div>
                    </div>

                    <div className="p-3 bg-indigo-900/20 rounded-lg border border-indigo-500/20 flex items-center justify-between">
                        <div className="flex gap-3 items-center">
                            <div className="p-2 bg-indigo-500/20 rounded-full">
                                <Code className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-indigo-300 block">State Injection</span>
                                <span className="text-[10px] text-slate-400">Permite a las tools modificar el contexto global.</span>
                            </div>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="State Injection Toggle"
                            checked={config.stateInjectionEnabled}
                            onChange={(e) => update('stateInjectionEnabled', e.target.checked)}
                            className="toggle-checkbox"
                        />
                    </div>
                </div>
            </Accordion>
        </div>
    )
}
