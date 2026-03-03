import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateTwilioConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { TwilioConfig } from '@/types/config'
import { Phone } from 'lucide-react'
import { api } from '@/services/api'
import { Accordion } from '@/components/ui/Accordion'
import { useTranslation } from '@/i18n/I18nContext'

export const TwilioConnectivitySettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const { twilio } = useAppSelector(state => state.config)

    // Control de Acordeones
    const [openSection, setOpenSection] = useState<string | null>('keys')

    // Test Call State
    const [testTarget, setTestTarget] = useState('')
    const [callStatus, setCallStatus] = useState<string | null>(null)
    const activeAgent = useAppSelector(state => state.agents.activeAgent)

    const updateTwilio = <K extends keyof TwilioConfig>(key: K, value: TwilioConfig[K]) => {
        dispatch(updateTwilioConfigState({ [key]: value }))
    }

    const handleTestCall = async () => {
        if (!testTarget || !activeAgent?.agent_uuid) return
        setCallStatus('Calling...')
        try {
            const res = await api.post<{ status: string, call_id?: string, detail?: string }>('/telephony/outbound', {
                agent_id: activeAgent.agent_uuid,
                to_number: testTarget,
                provider: 'twilio'
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
        <div className="space-y-4">
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
                {/* Twilio Credentials Card */}
                <div className="p-4 rounded-xl border border-red-500/20 bg-slate-900/50 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-2 opacity-5">
                        <Phone className="w-16 h-16 text-red-500" />
                    </div>
                    <h4 className="text-sm font-bold text-red-400 mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500"></span> Twilio (Phone)
                    </h4>
                    <div className="space-y-4 relative z-10 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="md:col-span-2">
                            <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Credentials</label>
                            <div className="flex items-center gap-2 px-3 py-2 bg-slate-900/80 rounded border border-white/5">
                                <span className="text-xs text-red-400 font-mono">🔒 {t('connectivity.env_configured')}</span>
                            </div>
                        </div>
                        <div className="md:col-span-2">
                            <Input
                                aria-label="Twilio From Number"
                                label={t('connectivity.from_number')}
                                value={twilio.twilioFromNumber}
                                onChange={(e) => updateTwilio('twilioFromNumber', e.target.value)}
                                placeholder="+1234567890"
                                className="font-mono text-xs border-l-4 border-l-red-500"
                            />
                        </div>

                        {/* Test Driver Widget */}
                        <div className="md:col-span-2 mt-2 pt-3 border-t border-red-500/20">
                            <label className="text-[10px] uppercase text-red-500 font-bold block mb-2">🚑 {t('connectivity.test_driver')}</label>
                            <div className="flex gap-2">
                                <Input
                                    aria-label="Test Call Target"
                                    value={testTarget}
                                    onChange={(e) => setTestTarget(e.target.value)}
                                    placeholder={t('connectivity.test_target_placeholder')}
                                    className="font-mono text-xs bg-black/40"
                                />
                                <button
                                    onClick={handleTestCall}
                                    disabled={!testTarget || !activeAgent}
                                    className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded shadow-lg shadow-red-900/20 transition-all flex items-center gap-2 disabled:opacity-50"
                                >
                                    <span>📞</span> {t('connectivity.call_btn')}
                                </button>
                            </div>
                            {callStatus && <span className="text-[10px] text-slate-400 mt-2 block">{callStatus}</span>}
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
                    {/* Twilio SIP */}
                    <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                        <h5 className="text-xs font-bold text-slate-300 mb-3 block">{t('connectivity.twilio_sip_trunk')}</h5>
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
                                    autoComplete="off"
                                />
                                <Input
                                    aria-label="Twilio SIP Pass"
                                    type="password"
                                    placeholder={t('connectivity.pass_label')}
                                    value={twilio.sipAuthPassPhone}
                                    onChange={(e) => updateTwilio('sipAuthPassPhone', e.target.value)}
                                    className="text-xs font-mono"
                                    autoComplete="new-password"
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
                                    <option value="us-east-1">{t('connectivity.region_us_east_1')}</option>
                                    <option value="us-west-1">{t('connectivity.region_us_west_1')}</option>
                                    <option value="eu-west-1">{t('connectivity.region_eu_west_1')}</option>
                                </Select>
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
                <div className="space-y-6">
                    {/* RECORDING */}
                    <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5">
                        <h5 className="text-xs font-bold text-white mb-4">{t('connectivity.recording_title')}</h5>
                        <div className="flex items-center justify-between pb-3 border-b border-white/5">
                            <span className="text-xs text-slate-300 font-bold">Twilio</span>
                            <div className="flex items-center gap-3">
                                <Select
                                    aria-label="Twilio Recording Channels"
                                    value={twilio.recordingChannelsPhone}
                                    onChange={(e) => updateTwilio('recordingChannelsPhone', e.target.value as 'mono' | 'dual')}
                                    className="text-xs"
                                >
                                    <option value="mono">{t('connectivity.recording_mono')}</option>
                                    <option value="dual">{t('connectivity.recording_dual')}</option>
                                </Select>
                                <input
                                    type="checkbox"
                                    checked={twilio.recordingEnabledPhone}
                                    onChange={(e) => updateTwilio('recordingEnabledPhone', e.target.checked)}
                                    className="w-4 h-4 rounded border-white/10 bg-black/20 text-pink-500"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* COMPLIANCE */}
                        <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-2 opacity-10"><span className="text-4xl">🛡️</span></div>
                            <h5 className="text-xs font-bold text-white mb-4 relative z-10">{t('connectivity.compliance_title')}</h5>
                            <div className="flex flex-col gap-3 relative z-10">
                                <label className="flex items-center justify-between p-3 rounded bg-black/20 border border-white/5 cursor-pointer hover:border-blue-500/30 transition-colors">
                                    <span className="text-xs text-slate-300">{t('connectivity.hipaa_twilio')}</span>
                                    <input
                                        type="checkbox"
                                        checked={twilio.hipaaEnabledPhone}
                                        onChange={(e) => updateTwilio('hipaaEnabledPhone', e.target.checked)}
                                        className="w-4 h-4 rounded border-white/10 bg-black/20 text-blue-500"
                                    />
                                </label>
                                <span className="text-[10px] text-slate-500 text-center mt-2">{t('connectivity.hipaa_desc')}</span>
                            </div>
                        </div>

                        {/* ADVANCED */}
                        <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 relative overflow-hidden">
                            <h5 className="text-xs font-bold text-white mb-4">{t('connectivity.advanced_title')}</h5>
                            <div className="flex flex-col gap-3">
                                <label className="flex items-center justify-between p-3 rounded bg-black/20 border border-white/5 cursor-pointer hover:border-pink-500/30 transition-colors">
                                    <span className="text-xs text-slate-300">{t('connectivity.dtmf_twilio')}</span>
                                    <input
                                        type="checkbox"
                                        checked={twilio.dtmfListeningEnabledPhone}
                                        onChange={(e) => updateTwilio('dtmfListeningEnabledPhone', e.target.checked)}
                                        className="w-4 h-4 rounded border-white/10 bg-black/20 text-pink-500"
                                    />
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </Accordion>
        </div>
    )
}
