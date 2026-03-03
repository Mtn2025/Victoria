import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Accordion } from '@/components/ui/Accordion'
import { Globe, Code, FileJson, Lock, FlaskConical, AlertTriangle } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

export const ToolsSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()

    // Obtenemos el profile activo del store general
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
            alert(t('tools.invalid_json'))
        }
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Header section */}
            <div className="flex justify-between items-center relative mb-4">
                <div>
                    <h3 className="text-lg font-medium text-white flex items-center gap-2">
                        <Code className="w-5 h-5 text-amber-500" />
                        {t('tools.title')}
                    </h3>
                    <p className="text-xs text-slate-400 mt-2">{t('tools.subtitle')}</p>
                </div>
            </div>

            {/* 1. Server (n8n / Webhook) */}
            <Accordion
                isOpen={openSection === 'server'}
                onToggle={() => setOpenSection(openSection === 'server' ? null : 'server')}
                className="border-pink-500/30"
                headerClassName="hover:bg-pink-900/20"
                title={
                    <span className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        {t('tools.server_title')}
                    </span>
                }
            >
                <div className="space-y-5 pt-2">
                    <Input
                        aria-label="Server URL"
                        label={t('tools.server_url')}
                        value={config.toolServerUrl}
                        onChange={(e) => update('toolServerUrl', e.target.value)}
                        placeholder="https://primary.n8n.com/webhook/..."
                        className="font-mono text-xs border-l-4 border-l-pink-500 bg-slate-800/50"
                        autoComplete="off"
                    />
                    <Input
                        aria-label="Server Secret"
                        type="password"
                        label={t('tools.server_secret')}
                        value={config.toolServerSecret}
                        onChange={(e) => update('toolServerSecret', e.target.value)}
                        placeholder="Bearer sk-..."
                        className="font-mono text-xs bg-slate-800/50"
                        autoComplete="new-password"
                    />
                    <div className="grid grid-cols-2 gap-6 bg-slate-800/30 p-4 rounded-lg border border-slate-700/50">
                        <Input
                            aria-label="Timeout"
                            type="number"
                            label={t('tools.timeout')}
                            value={config.toolTimeoutMs}
                            onChange={(e) => update('toolTimeoutMs', parseInt(e.target.value))}
                            className="font-mono text-xs text-center bg-slate-900/50"
                        />
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1 mb-2 block">{t('tools.retry_error')}</label>
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
                        className="text-xs font-mono italic text-red-300 border-red-900/30 bg-red-950/20"
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
                        {t('tools.tab_schema')}
                    </span>
                }
            >
                <div className="space-y-4 pt-2">
                    <div className="bg-slate-900/80 rounded-lg border border-slate-700 overflow-hidden shadow-inner">
                        <div className="bg-slate-800 px-4 py-3 flex justify-between items-center border-b border-slate-700/50">
                            <span className="text-xs font-mono text-amber-400 tracking-wider font-bold">{t('tools.schema_filename')}</span>
                            <button
                                onClick={handlePrettify}
                                className="text-[10px] bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded text-white transition font-bold"
                            >
                                {t('tools.prettify')}
                            </button>
                        </div>
                        <div className="bg-amber-900/10 p-3 flex gap-2 items-start border-b border-amber-900/30">
                            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                            <p className="text-[11px] text-amber-200/70 tracking-wide">
                                {t('tools.schema_desc').replace('⚠ ', '')}
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                        <div className="flex items-center justify-between bg-slate-800/40 p-4 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors">
                            <div className="pr-4">
                                <span className="text-sm font-bold text-slate-200 block mb-1">{t('tools.async_exec')}</span>
                                <span className="text-[10px] text-slate-500 leading-tight">{t('tools.async_desc')}</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Async Execution Toggle"
                                checked={config.asyncTools}
                                onChange={(e) => update('asyncTools', e.target.checked)}
                                className="toggle-checkbox shrink-0"
                            />
                        </div>

                        <div className="flex items-center justify-between bg-blue-900/10 p-4 rounded-xl border border-blue-500/20 hover:border-blue-500/30 transition-colors">
                            <div className="pr-4">
                                <span className="text-sm font-bold text-blue-300 block mb-1">{t('tools.client_tools')}</span>
                                <span className="text-[10px] text-blue-400/60 leading-tight">{t('tools.client_tools_desc')}</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Client Tools Toggle"
                                checked={config.clientToolsEnabled}
                                onChange={(e) => update('clientToolsEnabled', e.target.checked)}
                                className="toggle-checkbox shrink-0"
                            />
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* 3. Security */}
            <Accordion
                isOpen={openSection === 'security'}
                onToggle={() => setOpenSection(openSection === 'security' ? null : 'security')}
                className="border-emerald-500/30"
                headerClassName="hover:bg-emerald-900/20"
                title={
                    <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        {t('tools.tab_security')}
                    </span>
                }
            >
                <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/50 shadow-sm relative group hover:border-emerald-500/30 transition-colors">
                            <h5 className="text-xs font-bold text-slate-300 mb-1">{t('tools.param_redac')}</h5>
                            <p className="text-[10px] text-slate-500 mb-3 leading-tight">{t('tools.param_redac_desc')}</p>
                            <textarea
                                aria-label="Parameter Redaction"
                                value={config.redactParams}
                                onChange={(e) => update('redactParams', e.target.value)}
                                className="w-full h-24 bg-black/40 border border-slate-700 rounded p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 custom-scrollbar shadow-inner"
                                placeholder='["password", "credit_card", "ssn"]'
                            />
                        </div>
                        <div className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/50 shadow-sm relative group hover:border-emerald-500/30 transition-colors">
                            <h5 className="text-xs font-bold text-slate-300 mb-1">{t('tools.transfer_whitelist')}</h5>
                            <p className="text-[10px] text-slate-500 mb-3 leading-tight">{t('tools.transfer_whitelist_desc')}</p>
                            <textarea
                                aria-label="Transfer Whitelist"
                                value={config.transferWhitelist}
                                onChange={(e) => update('transferWhitelist', e.target.value)}
                                className="w-full h-24 bg-black/40 border border-slate-700 rounded p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 custom-scrollbar shadow-inner"
                                placeholder='["+15550123", "+15550124"]'
                            />
                        </div>
                    </div>

                    <div className="bg-indigo-900/10 p-4 rounded-xl border border-indigo-500/20 flex items-center justify-between hover:border-indigo-500/30 transition-colors">
                        <div className="flex gap-4 items-center pr-4">
                            <div className="p-2.5 bg-indigo-500/10 rounded-full shrink-0">
                                <FlaskConical className="w-5 h-5 text-indigo-400" />
                            </div>
                            <div>
                                <span className="text-sm font-bold text-indigo-300 block mb-1">{t('tools.state_injection')}</span>
                                <span className="text-[10px] text-indigo-200/50 leading-tight">{t('tools.state_injection_desc')}</span>
                            </div>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="State Injection Toggle"
                            checked={config.stateInjectionEnabled}
                            onChange={(e) => update('stateInjectionEnabled', e.target.checked)}
                            className="toggle-checkbox shrink-0"
                        />
                    </div>
                </div>
            </Accordion>
        </div>
    )
}
