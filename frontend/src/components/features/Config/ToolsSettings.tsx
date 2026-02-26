import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Globe, Code, FileJson, Lock, Zap } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

type TabType = 'schema' | 'server' | 'security'

export const ToolsSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()

    // Obtenemos el profile activo del store general (ya no usamos estado local)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser, twilio, telnyx } = useAppSelector(state => state.config)

    // Controlamos el Tab abierto
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
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                    <Code className="w-6 h-6 text-amber-500" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">{t('tools.title')}</h2>
                    <p className="text-sm text-slate-400">{t('tools.subtitle')}</p>
                </div>
            </div>

            {/* Sub-Navigation Tabs */}
            <div className="bg-slate-900/50 p-1 rounded-xl flex gap-1 border border-slate-800">
                <button
                    onClick={() => setActiveTab('schema')}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-bold rounded-lg transition-all ${activeTab === 'schema' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800'}`}
                >
                    <FileJson className="w-4 h-4 text-amber-400" />
                    {t('tools.tab_schema')}
                </button>
                <button
                    onClick={() => setActiveTab('server')}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-bold rounded-lg transition-all ${activeTab === 'server' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800'}`}
                >
                    <Globe className="w-4 h-4 text-pink-400" />
                    {t('tools.tab_server')}
                </button>
                <button
                    onClick={() => setActiveTab('security')}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-bold rounded-lg transition-all ${activeTab === 'security' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800'}`}
                >
                    <Lock className="w-4 h-4 text-amber-500" />
                    {t('tools.tab_security')}
                </button>
            </div>

            {/* Tab Contents */}

            {/* 1. JSON Schema Content */}
            {activeTab === 'schema' && (
                <div className="space-y-4 animate-in fade-in duration-300">
                    <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                        <div className="bg-slate-800 px-4 py-3 flex justify-between items-center border-b border-slate-700">
                            <span className="text-sm font-mono font-bold text-amber-400">{t('tools.schema_filename')}</span>
                            <button
                                onClick={handlePrettify}
                                className="text-[11px] bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md text-white transition font-bold tracking-wide uppercase"
                            >
                                {t('tools.prettify')}
                            </button>
                        </div>
                        <div className="bg-amber-900/10 p-3 border-b border-amber-900/30">
                            <p className="text-xs font-semibold text-amber-500/80">
                                {t('tools.schema_desc')}
                            </p>
                        </div>
                        <textarea
                            aria-label="JSON Schema Editor"
                            value={config.toolsSchema}
                            onChange={(e) => update('toolsSchema', e.target.value)}
                            className="w-full h-[320px] bg-[#0f111a] text-[13px] font-mono leading-relaxed text-slate-300 p-5 focus:outline-none resize-none custom-scrollbar"
                            placeholder='[{ "type": "function", ... }]'
                            spellCheck={false}
                        />
                    </div>

                    <label className={`flex items-center justify-between p-4 cursor-pointer rounded-xl border transition-all duration-200 ${config.asyncTools ? 'border-slate-600 bg-slate-800' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'}`}>
                        <div>
                            <span className="text-sm font-bold text-white block">{t('tools.async_exec')}</span>
                            <span className="text-xs text-slate-400 mt-1 block">{t('tools.async_desc')}</span>
                        </div>
                        <div className="flex items-center h-5">
                            <input
                                type="checkbox"
                                className="toggle-checkbox"
                                checked={config.asyncTools}
                                onChange={(e) => update('asyncTools', e.target.checked)}
                            />
                        </div>
                    </label>
                </div>
            )}

            {/* 2. Server (n8n / Webhook) Content */}
            {activeTab === 'server' && (
                <div className="space-y-6 animate-in fade-in duration-300 bg-slate-900/30 p-5 rounded-2xl border border-slate-800/50">
                    <h3 className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4" />
                        {t('tools.server_title')}
                    </h3>

                    <div className="space-y-4">
                        <Input
                            aria-label="Server URL"
                            label={t('tools.server_url')}
                            value={config.toolServerUrl}
                            onChange={(e) => update('toolServerUrl', e.target.value)}
                            placeholder="https://primary.n8n.com/webhook/..."
                            className="font-mono text-[13px] border-l-4 border-l-pink-500 bg-slate-900"
                        />
                        <Input
                            aria-label="Server Secret"
                            type="password"
                            label={t('tools.server_secret')}
                            value={config.toolServerSecret}
                            onChange={(e) => update('toolServerSecret', e.target.value)}
                            placeholder="Bearer sk-..."
                            className="font-mono text-[13px] bg-slate-900"
                        />
                        <div className="grid grid-cols-2 gap-4">
                            <Input
                                aria-label="Timeout"
                                type="number"
                                label={t('tools.timeout')}
                                value={config.toolTimeoutMs}
                                onChange={(e) => update('toolTimeoutMs', parseInt(e.target.value))}
                                className="font-mono text-[13px] text-center bg-slate-900"
                            />
                            <div>
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">{t('tools.retry_error')}</label>
                                <Select
                                    aria-label="Retry Count"
                                    value={config.toolRetryCount}
                                    onChange={(e) => update('toolRetryCount', parseInt(e.target.value))}
                                    className="bg-slate-900 w-full"
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
                            className="text-[13px] italic text-red-300 border-red-900/30 bg-red-950/10 focus:border-red-500 focus:ring-red-500"
                        />
                    </div>

                    <label className={`mt-6 flex items-center justify-between p-4 cursor-pointer rounded-xl border transition-all duration-200 ${config.clientToolsEnabled ? 'border-blue-500/50 bg-blue-900/20' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'}`}>
                        <div>
                            <span className="text-sm font-bold text-blue-300 block">{t('tools.client_tools')}</span>
                            <span className="text-xs text-blue-200/50 mt-1 block">{t('tools.client_tools_desc')}</span>
                        </div>
                        <div className="flex items-center h-5">
                            <input
                                type="checkbox"
                                className="toggle-checkbox"
                                checked={config.clientToolsEnabled}
                                onChange={(e) => update('clientToolsEnabled', e.target.checked)}
                            />
                        </div>
                    </label>
                </div>
            )}

            {/* 3. Security Content */}
            {activeTab === 'security' && (
                <div className="space-y-4 animate-in fade-in duration-300">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700">
                            <h5 className="text-sm font-bold text-slate-200 mb-1">{t('tools.param_redac')}</h5>
                            <p className="text-xs text-slate-500 mb-3">{t('tools.param_redac_desc')}</p>
                            <textarea
                                aria-label="Parameter Redaction"
                                value={config.redactParams}
                                onChange={(e) => update('redactParams', e.target.value)}
                                className="w-full h-24 bg-[#0f111a] border border-white/5 rounded-lg p-3 text-[13px] font-mono focus:outline-none focus:border-amber-500/50 custom-scrollbar text-amber-200/70"
                                placeholder='["password", "credit_card", "ssn"]'
                            />
                        </div>
                        <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700">
                            <h5 className="text-sm font-bold text-slate-200 mb-1">{t('tools.transfer_whitelist')}</h5>
                            <p className="text-xs text-slate-500 mb-3">{t('tools.transfer_whitelist_desc')}</p>
                            <textarea
                                aria-label="Transfer Whitelist"
                                value={config.transferWhitelist}
                                onChange={(e) => update('transferWhitelist', e.target.value)}
                                className="w-full h-24 bg-[#0f111a] border border-white/5 rounded-lg p-3 text-[13px] font-mono focus:outline-none focus:border-amber-500/50 custom-scrollbar text-amber-200/70"
                                placeholder='["+15550123", "+15550124"]'
                            />
                        </div>
                    </div>

                    <label className={`flex items-center justify-between p-5 cursor-pointer rounded-xl border transition-all duration-200 ${config.stateInjectionEnabled ? 'border-indigo-500/50 bg-indigo-900/20' : 'border-indigo-500/10 bg-indigo-900/10 hover:border-indigo-500/20'}`}>
                        <div className="flex gap-4 items-center">
                            <div className={`p-3 rounded-full transition-colors ${config.stateInjectionEnabled ? 'bg-indigo-500/30' : 'bg-indigo-500/10'}`}>
                                <Code className={`w-5 h-5 ${config.stateInjectionEnabled ? 'text-indigo-300' : 'text-indigo-500/50'}`} />
                            </div>
                            <div>
                                <span className="text-sm font-bold text-indigo-300 block">{t('tools.state_injection')}</span>
                                <span className="text-xs text-indigo-200/50 mt-1 block">{t('tools.state_injection_desc')}</span>
                            </div>
                        </div>
                        <div className="flex items-center h-5">
                            <input
                                type="checkbox"
                                className="toggle-checkbox"
                                checked={config.stateInjectionEnabled}
                                onChange={(e) => update('stateInjectionEnabled', e.target.checked)}
                            />
                        </div>
                    </label>
                </div>
            )}
        </div>
    )
}

