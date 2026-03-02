import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Globe, Code, FileJson, Lock, Zap, FlaskConical, AlertTriangle } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

type TabType = 'schema' | 'server' | 'security'

export const ToolsSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()

    // Obtenemos el profile activo del store general (ya no usamos estado local)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser, twilio, telnyx } = useAppSelector(state => state.config)

    // Controlamos la pestaña activa
    const [activeTab, setActiveTab] = useState<TabType>('schema')

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
            alert(t('tools.invalid_json'))
        }
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Header */}
            <div className="flex items-center gap-3 relative mb-6">
                <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20">
                    <Code className="w-6 h-6 text-amber-500" />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-white tracking-tight">
                        {t('tools.title')}
                    </h3>
                    <p className="text-sm text-slate-400">
                        {t('tools.subtitle')}
                    </p>
                </div>
            </div>

            {/* Tabs Selector */}
            <div className="flex bg-slate-800/80 rounded-lg p-1 shadow-inner border border-slate-700/50">
                <button
                    onClick={() => setActiveTab('schema')}
                    className={`flex-1 py-2 px-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${activeTab === 'schema'
                        ? 'bg-slate-600/50 text-amber-400 shadow-sm'
                        : 'text-slate-400 hover:text-amber-200/80 hover:bg-slate-700/30'
                        }`}
                >
                    <FileJson className="w-4 h-4" />
                    {t('tools.tab_schema')}
                </button>
                <button
                    onClick={() => setActiveTab('server')}
                    className={`flex-1 py-2 px-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${activeTab === 'server'
                        ? 'bg-slate-600/50 text-pink-400 shadow-sm'
                        : 'text-slate-400 hover:text-pink-200/80 hover:bg-slate-700/30'
                        }`}
                >
                    <Globe className="w-4 h-4" />
                    {t('tools.tab_server')}
                </button>
                <button
                    onClick={() => setActiveTab('security')}
                    className={`flex-1 py-2 px-2 rounded-md text-xs font-bold transition-all flex items-center justify-center gap-2 ${activeTab === 'security'
                        ? 'bg-slate-600/50 text-emerald-400 shadow-sm'
                        : 'text-slate-400 hover:text-emerald-200/80 hover:bg-slate-700/30'
                        }`}
                >
                    <Lock className="w-4 h-4" />
                    {t('tools.tab_security')}
                </button>
            </div>

            {/* Content Area */}
            <div className="mt-4 animate-in fade-in zoom-in-95 duration-200">
                {/* 1. JSON Schema Content */}
                {activeTab === 'schema' && (
                    <div className="space-y-4">
                        <div className="bg-slate-900/50 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
                            <div className="bg-slate-800/80 px-4 py-3 flex justify-between items-center border-b border-slate-700/50">
                                <span className="text-sm font-bold font-mono text-amber-400">{t('tools.schema_filename')}</span>
                                <button
                                    onClick={handlePrettify}
                                    className="text-[11px] bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md text-slate-200 transition font-bold tracking-wide"
                                >
                                    {t('tools.prettify')}
                                </button>
                            </div>
                            <div className="bg-amber-900/10 p-3 border-b border-amber-900/30 flex gap-2 items-start">
                                <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                                <p className="text-xs text-amber-200/70 font-medium tracking-wide">
                                    {t('tools.schema_desc').replace('⚠ ', '')}
                                </p>
                            </div>
                            <textarea
                                aria-label="JSON Schema Editor"
                                value={config.toolsSchema}
                                onChange={(e) => update('toolsSchema', e.target.value)}
                                className="w-full h-80 bg-[#0B1121] text-xs font-mono text-slate-300 p-4 focus:outline-none resize-none custom-scrollbar shadow-inner"
                                placeholder='[
  {
    "type": "function",
    "function": {
      "name": "check_order_status",
      "description": "Check the status of an order",
      "parameters": { ... }
    }
  }
]'
                            />
                        </div>

                        <div className="flex items-center justify-between bg-slate-800/40 p-5 rounded-xl border border-slate-700/50 shadow-sm hover:border-slate-600 transition-colors">
                            <div>
                                <span className="text-sm font-bold text-slate-200 block">{t('tools.async_exec')}</span>
                                <span className="text-[11px] text-slate-500 mt-1 block">{t('tools.async_desc')}</span>
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

                {/* 2. Server (n8n) Content */}
                {activeTab === 'server' && (
                    <div className="space-y-4">
                        <div className="bg-slate-800/40 rounded-xl border border-slate-700/50 shadow-sm overflow-hidden p-6 space-y-6">
                            <div className="flex items-center gap-2 mb-2">
                                <Zap className="w-5 h-5 text-pink-500" />
                                <h4 className="text-lg font-bold text-white">{t('tools.server_title')}</h4>
                            </div>

                            <div className="space-y-5">
                                <Input
                                    aria-label="Server URL"
                                    label={t('tools.server_url')}
                                    value={config.toolServerUrl}
                                    onChange={(e) => update('toolServerUrl', e.target.value)}
                                    placeholder="https://primary.n8n.com/webhook/..."
                                    className="font-mono text-xs border-l-4 border-l-pink-500 bg-slate-900/50"
                                />
                                <Input
                                    aria-label="Server Secret"
                                    type="password"
                                    label={t('tools.server_secret')}
                                    value={config.toolServerSecret}
                                    onChange={(e) => update('toolServerSecret', e.target.value)}
                                    placeholder="Bearer sk-..."
                                    className="font-mono text-xs bg-slate-900/50"
                                />
                                <div className="grid grid-cols-2 gap-6">
                                    <Input
                                        aria-label="Timeout"
                                        type="number"
                                        label={t('tools.timeout')}
                                        value={config.toolTimeoutMs}
                                        onChange={(e) => update('toolTimeoutMs', parseInt(e.target.value))}
                                        className="font-mono text-xs text-center font-bold bg-slate-900/50"
                                    />
                                    <div>
                                        <label className="text-[10px] uppercase text-slate-400 font-bold tracking-wider block mb-1.5">{t('tools.retry_error')}</label>
                                        <Select
                                            aria-label="Retry Count"
                                            value={config.toolRetryCount}
                                            onChange={(e) => update('toolRetryCount', parseInt(e.target.value))}
                                        >
                                            <option value={0}>{t('tools.retry_disabled')}</option>
                                            <option value={1}>{t('tools.retry_1')}</option>
                                            <option value={2}>{t('tools.retry_2')}</option>
                                        </Select>
                                    </div>
                                </div>
                                <Input
                                    aria-label="Error Message"
                                    label={t('tools.error_msg')}
                                    value={config.toolErrorMsg}
                                    onChange={(e) => update('toolErrorMsg', e.target.value)}
                                    className="text-xs font-mono italic text-red-400 bg-red-950/20 border-red-900/50"
                                    placeholder="Lo siento, hubo un error técnico."
                                />
                            </div>
                        </div>

                        <div className="flex items-center justify-between bg-[#0f172a] p-5 rounded-xl border border-blue-500/20 shadow-sm hover:border-blue-500/30 transition-colors mt-2">
                            <div>
                                <span className="text-sm font-bold text-blue-400 block">{t('tools.client_tools')}</span>
                                <span className="text-[11px] text-blue-400/60 mt-1 block">{t('tools.client_tools_desc')}</span>
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

                {/* 3. Security Content */}
                {activeTab === 'security' && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-slate-800/40 p-5 rounded-xl border border-slate-700/50 shadow-sm">
                                <h5 className="text-sm font-bold text-slate-200 mb-1">{t('tools.param_redac')}</h5>
                                <p className="text-[11px] text-slate-500 mb-4 tracking-wide">{t('tools.param_redac_desc')}</p>
                                <textarea
                                    aria-label="Parameter Redaction"
                                    value={config.redactParams}
                                    onChange={(e) => update('redactParams', e.target.value)}
                                    className="w-full h-32 bg-black/40 border border-slate-700 rounded-lg p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 custom-scrollbar"
                                    placeholder='["password", "credit_card", "ssn"]'
                                />
                            </div>
                            <div className="bg-slate-800/40 p-5 rounded-xl border border-slate-700/50 shadow-sm">
                                <h5 className="text-sm font-bold text-slate-200 mb-1">{t('tools.transfer_whitelist')}</h5>
                                <p className="text-[11px] text-slate-500 mb-4 tracking-wide">{t('tools.transfer_whitelist_desc')}</p>
                                <textarea
                                    aria-label="Transfer Whitelist"
                                    value={config.transferWhitelist}
                                    onChange={(e) => update('transferWhitelist', e.target.value)}
                                    className="w-full h-32 bg-black/40 border border-slate-700 rounded-lg p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 custom-scrollbar"
                                    placeholder='["+15550123", "+15550124"]'
                                />
                            </div>
                        </div>

                        <div className="flex items-center justify-between bg-indigo-950/20 p-5 rounded-xl border border-indigo-500/20 shadow-sm hover:border-indigo-500/30 transition-colors">
                            <div className="flex gap-4 items-center">
                                <div className="p-2.5 bg-indigo-500/10 rounded-full shrink-0">
                                    <FlaskConical className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <span className="text-sm font-bold text-indigo-300 block">{t('tools.state_injection')}</span>
                                    <span className="text-[11px] text-slate-400 mt-1 block">{t('tools.state_injection_desc')}</span>
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
                )}
            </div>
        </div>
    )
}
