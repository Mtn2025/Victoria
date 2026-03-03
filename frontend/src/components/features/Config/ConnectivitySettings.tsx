import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { TwilioConfig, TelnyxConfig } from '@/types/config'
import { Network, Server, Phone, Shield } from 'lucide-react'
import { api } from '@/services/api'
import { Accordion } from '@/components/ui/Accordion'
import { useTranslation } from '@/i18n/I18nContext'

export const ConnectivitySettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const { twilio, telnyx } = useAppSelector(state => state.config)

    // Control de Acordeones
    const [openSection, setOpenSection] = useState<string | null>('keys')

    // Test Call State
    const [testTarget, setTestTarget] = useState('')
    const [callStatus, setCallStatus] = useState<string | null>(null)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const activeAgent = useAppSelector(state => state.agents.activeAgent)

    const updateTwilio = <K extends keyof TwilioConfig>(key: K, value: TwilioConfig[K]) => {
        dispatch(updateTwilioConfigState({ [key]: value }))
    }

    const updateTelnyx = <K extends keyof TelnyxConfig>(key: K, value: TelnyxConfig[K]) => {
        dispatch(updateTelnyxConfigState({ [key]: value }))
    }

    const handleTestCall = async (provider: string) => {
        if (!testTarget || !activeAgent?.agent_uuid) return
        setCallStatus('Calling...')
        try {
            const res = await api.post<{ status: string, call_id?: string, detail?: string }>('/telephony/outbound', {
                agent_id: activeAgent.agent_uuid,
                to_number: testTarget,
                provider: provider
            })
            if (res.status === 'success') {
                setCallStatus(`Calling... ID: ${res.call_id}`)
            } else {
                setCallStatus(`Error: ${res.detail}`)
            }
        } catch (e: unknown) {
            setCallStatus(`Fail: ${(e as Error).message}`)
        }
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Header */}
            <div className="flex justify-between items-center relative mb-4">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Network className="w-5 h-5 text-emerald-400" />
                    {t('connectivity.title')}
                </h3>
            </div>

            {/* 1. Content: Keys / Credentials */}
            <Accordion
                isOpen={openSection === 'keys'}
                onToggle={() => setOpenSection(openSection === 'keys' ? null : 'keys')}
                className="border-amber-500/30"
                headerClassName="hover:bg-amber-900/20"
                title={
                    <span className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                        🔑 {t('connectivity.accordion_keys')}
                    </span>
                }
            >
                <div className="space-y-4">
                    {/* Twilio */}
                    <div className="p-4 rounded-xl border border-red-500/20 bg-slate-900/50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-5">
                            <Phone className="w-16 h-16 text-red-500" />
                        </div>
                        <h4 className="text-sm font-bold text-red-400 mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span> Twilio (Phone)
                        </h4>
                        <div className="space-y-4 relative z-10">
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Credentials</label>
                                <div className="flex items-center gap-2 px-3 py-2 bg-slate-900/80 rounded border border-white/5">
                                    <span className="text-xs text-red-400 font-mono">🔒 {t('connectivity.env_configured')}</span>
                                </div>
                            </div>
                            <div>
                                <Input
                                    aria-label="Twilio From Number"
                                    label={t('connectivity.from_number')}
                                    value={twilio.twilioFromNumber}
                                    onChange={(e) => updateTwilio('twilioFromNumber', e.target.value)}
                                    placeholder="+1234567890"
                                    className="font-mono text-xs border-l-4 border-l-red-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Telnyx */}
                    <div className="p-4 rounded-xl border border-emerald-500/20 bg-slate-900/50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-5">
                            <Server className="w-16 h-16 text-emerald-500" />
                        </div>
                        <h4 className="text-sm font-bold text-emerald-400 mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Telnyx
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
                            <div className="md:col-span-2">
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Credentials</label>
                                <div className="flex items-center gap-2 px-3 py-2 bg-slate-900/80 rounded border border-white/5">
                                    <span className="text-xs text-emerald-400 font-mono">🔒 API Key {t('connectivity.env_configured').replace('Configured ', '')}</span>
                                </div>
                            </div>
                            <div>
                                <Input
                                    aria-label="SIP Connection ID"
                                    label={t('connectivity.sip_conn_id')}
                                    value={telnyx.telnyxConnectionId}
                                    onChange={(e) => updateTelnyx('telnyxConnectionId', e.target.value)}
                                    placeholder="Uuid"
                                    className="font-mono text-xs"
                                />
                            </div>
                            <div>
                                <Input
                                    aria-label="Caller ID Override"
                                    label={t('connectivity.caller_id_override')}
                                    value={telnyx.callerIdTelnyx}
                                    onChange={(e) => updateTelnyx('callerIdTelnyx', e.target.value)}
                                    placeholder="+1..."
                                    className="font-mono text-xs"
                                />
                            </div>

                            {/* Test Driver Widget */}
                            <div className="md:col-span-2 mt-2 pt-3 border-t border-emerald-500/20">
                                <label className="text-[10px] uppercase text-emerald-500 font-bold block mb-2">🚑 {t('connectivity.test_driver')}</label>
                                <div className="flex gap-2">
                                    <Input
                                        aria-label="Test Call Target"
                                        value={testTarget}
                                        onChange={(e) => setTestTarget(e.target.value)}
                                        placeholder={t('connectivity.test_target_placeholder')}
                                        className="font-mono text-xs bg-black/40"
                                    />
                                    <button
                                        onClick={() => handleTestCall(activeProfile === 'telnyx' ? 'telnyx' : (activeProfile === 'twilio' ? 'twilio' : 'unknown'))}
                                        disabled={!testTarget || !activeAgent || activeProfile === 'browser'}
                                        className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded shadow-lg shadow-emerald-900/20 transition-all flex items-center gap-2 disabled:opacity-50"
                                    >
                                        <span>📞</span> {t('connectivity.call_btn')}
                                    </button>
                                </div>
                                {callStatus && <span className="text-[10px] text-slate-400 mt-2 block">{callStatus}</span>}
                            </div>
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* 2. Content: SIP & Trunking */}
            <Accordion
                isOpen={openSection === 'sip'}
                onToggle={() => setOpenSection(openSection === 'sip' ? null : 'sip')}
                className="border-indigo-500/30"
                headerClassName="hover:bg-indigo-900/20"
                title={
                    <span className="text-sm font-bold text-indigo-400 uppercase tracking-wider">
                        📡 {t('connectivity.accordion_sip')}
                    </span>
                }
            >
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Twilio SIP */}
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                            <h5 className="text-xs font-bold text-slate-300 mb-3 block">Twilio SIP Trunking</h5>
                            <div className="space-y-3">
                                <Input
                                    aria-label="Twilio SIP Trunk URI"
                                    label={t('connectivity.sip_trunk_uri')}
                                    value={twilio.sipTrunkUriPhone}
                                    onChange={(e) => updateTwilio('sipTrunkUriPhone', e.target.value)}
                                    placeholder="sip:..."
                                    className="text-xs font-mono"
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <Input
                                        aria-label="Twilio SIP User"
                                        placeholder={t('connectivity.user_label')}
                                        value={twilio.sipAuthUserPhone}
                                        onChange={(e) => updateTwilio('sipAuthUserPhone', e.target.value)}
                                        className="text-xs font-mono"
                                    />
                                    <Input
                                        aria-label="Twilio SIP Pass"
                                        type="password"
                                        placeholder={t('connectivity.pass_label')}
                                        value={twilio.sipAuthPassPhone}
                                        onChange={(e) => updateTwilio('sipAuthPassPhone', e.target.value)}
                                        className="text-xs font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">{t('connectivity.geo_region')}</label>
                                    <Select
                                        aria-label="Twilio Geo Region"
                                        value={twilio.geoRegionPhone}
                                        onChange={(e) => updateTwilio('geoRegionPhone', e.target.value as 'us-east-1' | 'us-west-1' | 'eu-west-1')}
                                        className="text-xs"
                                    >
                                        <option value="us-east-1">US East (N. Virginia)</option>
                                        <option value="us-west-1">US West (Oregon)</option>
                                        <option value="eu-west-1">Europe (Ireland)</option>
                                    </Select>
                                </div>
                            </div>
                        </div>

                        {/* Telnyx SIP */}
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                            <h5 className="text-xs font-bold text-slate-300 mb-3 block">Telnyx SIP Trunking</h5>
                            <div className="space-y-3">
                                <Input
                                    aria-label="Telnyx SIP Trunk URI"
                                    label={t('connectivity.sip_trunk_uri')}
                                    value={telnyx.sipTrunkUriTelnyx}
                                    onChange={(e) => updateTelnyx('sipTrunkUriTelnyx', e.target.value)}
                                    placeholder="sip:..."
                                    className="text-xs font-mono"
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <Input
                                        aria-label="Telnyx SIP User"
                                        placeholder={t('connectivity.user_label')}
                                        value={telnyx.sipAuthUserTelnyx}
                                        onChange={(e) => updateTelnyx('sipAuthUserTelnyx', e.target.value)}
                                        className="text-xs font-mono"
                                    />
                                    <Input
                                        aria-label="Telnyx SIP Pass"
                                        type="password"
                                        placeholder={t('connectivity.pass_label')}
                                        value={telnyx.sipAuthPassTelnyx}
                                        onChange={(e) => updateTelnyx('sipAuthPassTelnyx', e.target.value)}
                                        className="text-xs font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">{t('connectivity.geo_region')}</label>
                                    <Select
                                        aria-label="Telnyx Geo Region"
                                        value={telnyx.geoRegionTelnyx}
                                        onChange={(e) => updateTelnyx('geoRegionTelnyx', e.target.value as 'us-central' | 'us-east' | 'global')}
                                        className="text-xs"
                                    >
                                        <option value="us-central">US Central (Chicago)</option>
                                        <option value="us-east">US East (Ashburn)</option>
                                        <option value="global">Global Anycast</option>
                                    </Select>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Fallback Number */}
                    <div className="bg-indigo-900/20 p-4 rounded-xl border border-indigo-500/20">
                        <label className="text-xs font-bold text-indigo-300 block mb-3">{t('connectivity.fallback_title')}</label>
                        <div className="flex flex-col sm:flex-row gap-4 items-center">
                            <Input
                                aria-label="Fallback Number"
                                value={twilio.fallbackNumberPhone}
                                onChange={(e) => updateTwilio('fallbackNumberPhone', e.target.value)}
                                placeholder="+1..."
                                className="w-full text-xs font-mono"
                            />
                            <span className="text-[10px] text-slate-400 w-full sm:w-auto shrink-0">{t('connectivity.fallback_desc')}</span>
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* 3. Content: Features & Call Options */}
            <Accordion
                isOpen={openSection === 'features'}
                onToggle={() => setOpenSection(openSection === 'features' ? null : 'features')}
                className="border-pink-500/30"
                headerClassName="hover:bg-pink-900/20"
                title={
                    <span className="text-sm font-bold text-pink-400 uppercase tracking-wider">
                        ⚙️ {t('connectivity.accordion_features')}
                    </span>
                }
            >
                <div className="space-y-4">
                    {/* Recording */}
                    <div className="p-4 rounded-xl border border-white/5 bg-slate-900/40">
                        <h5 className="text-xs font-bold text-white mb-4 block">{t('connectivity.recording_title')}</h5>

                        {/* Twilio */}
                        <div className="flex justify-between items-center py-3 border-b border-white/5">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
                                <span className="text-xs font-bold text-slate-300 w-24">Twilio</span>
                                <Select
                                    aria-label="Twilio Recording Channels"
                                    value={twilio.recordingChannelsPhone}
                                    onChange={(e) => updateTwilio('recordingChannelsPhone', e.target.value as 'mono' | 'dual')}
                                    className="h-8 text-[11px] w-40 bg-slate-800"
                                >
                                    <option value="mono">{t('connectivity.recording_mono')}</option>
                                    <option value="dual">{t('connectivity.recording_dual')}</option>
                                </Select>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Enable Twilio Recording"
                                checked={twilio.recordingEnabledPhone}
                                onChange={(e) => updateTwilio('recordingEnabledPhone', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>

                        {/* Telnyx */}
                        <div className="flex justify-between items-center py-3">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
                                <span className="text-xs font-bold text-slate-300 w-24">Telnyx</span>
                                <Select
                                    aria-label="Telnyx Recording Channels"
                                    value={telnyx.recordingChannelsTelnyx}
                                    onChange={(e) => updateTelnyx('recordingChannelsTelnyx', e.target.value as 'mono' | 'dual')}
                                    className="h-8 text-[11px] w-40 bg-slate-800"
                                >
                                    <option value="mono">{t('connectivity.recording_mono')}</option>
                                    <option value="dual">{t('connectivity.recording_dual')}</option>
                                </Select>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Enable Telnyx Recording"
                                checked={telnyx.enableRecordingTelnyx}
                                onChange={(e) => updateTelnyx('enableRecordingTelnyx', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>
                    </div>

                    {/* Compliance */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700">
                            <h5 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                                <Shield className="w-4 h-4 text-blue-400" />
                                {t('connectivity.compliance_title')}
                            </h5>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center bg-slate-900/50 px-3 py-2 rounded-lg border border-white/5">
                                    <span className="text-xs font-medium text-slate-300">{t('connectivity.hipaa_twilio')}</span>
                                    <input type="checkbox" aria-label="Enable Twilio HIPAA" checked={twilio.hipaaEnabledPhone} onChange={(e) => updateTwilio('hipaaEnabledPhone', e.target.checked)} className="toggle-checkbox" />
                                </div>
                                <div className="flex justify-between items-center bg-slate-900/50 px-3 py-2 rounded-lg border border-white/5">
                                    <span className="text-xs font-medium text-slate-300">{t('connectivity.hipaa_telnyx')}</span>
                                    <input type="checkbox" aria-label="Enable Telnyx HIPAA" checked={telnyx.hipaaEnabledTelnyx} onChange={(e) => updateTelnyx('hipaaEnabledTelnyx', e.target.checked)} className="toggle-checkbox" />
                                </div>
                                <p className="text-[10px] text-slate-500 text-center">{t('connectivity.hipaa_desc')}</p>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700">
                            <h5 className="text-sm font-bold text-slate-200 mb-4 block">{t('connectivity.advanced_title')}</h5>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center bg-slate-900/50 px-3 py-2 rounded-lg border border-white/5">
                                    <span className="text-xs font-medium text-slate-300">{t('connectivity.dtmf_twilio')}</span>
                                    <input type="checkbox" aria-label="Enable Twilio DTMF" checked={twilio.dtmfListeningEnabledPhone} onChange={(e) => updateTwilio('dtmfListeningEnabledPhone', e.target.checked)} className="toggle-checkbox" />
                                </div>
                                <div className="flex justify-between items-center bg-slate-900/50 px-3 py-2 rounded-lg border border-white/5">
                                    <span className="text-xs font-medium text-slate-300">{t('connectivity.dtmf_telnyx')}</span>
                                    <input type="checkbox" aria-label="Enable Telnyx DTMF" checked={telnyx.dtmfListeningEnabledTelnyx} onChange={(e) => updateTelnyx('dtmfListeningEnabledTelnyx', e.target.checked)} className="toggle-checkbox" />
                                </div>
                                <div className="pt-2">
                                    <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">{t('connectivity.amd_telnyx')}</label>
                                    <Select
                                        aria-label="Telnyx AMD Config"
                                        value={telnyx.amdConfig}
                                        onChange={(e) => updateTelnyx('amdConfig', e.target.value as 'disabled' | 'detect' | 'detect_hangup' | 'detect_message_end')}
                                        className="h-9 text-xs bg-slate-900 border-white/5"
                                    >
                                        <option value="disabled">{t('connectivity.amd_disabled')}</option>
                                        <option value="detect">{t('connectivity.amd_detect')}</option>
                                        <option value="detect_hangup">{t('connectivity.amd_detect_hangup')}</option>
                                        <option value="detect_message_end">{t('connectivity.amd_detect_message')}</option>
                                    </Select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </Accordion>
        </div>
    )
}

