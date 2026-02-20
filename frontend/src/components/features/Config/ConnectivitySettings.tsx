import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateTwilioConfigState, updateTelnyxConfigState } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { TwilioConfig, TelnyxConfig } from '@/types/config'
import { Network, Server, Phone, Shield } from 'lucide-react'
import { api } from '@/services/api'

export const ConnectivitySettings = () => {
    const dispatch = useAppDispatch()
    const { twilio, telnyx } = useAppSelector(state => state.config)
    const [subTab, setSubTab] = useState<'keys' | 'sip' | 'features'>('keys')

    // Test Call State
    const [testTarget, setTestTarget] = useState('')
    const [callStatus, setCallStatus] = useState<string | null>(null)

    const updateTwilio = <K extends keyof TwilioConfig>(key: K, value: TwilioConfig[K]) => {
        dispatch(updateTwilioConfigState({ [key]: value }))
    }

    const updateTelnyx = <K extends keyof TelnyxConfig>(key: K, value: TelnyxConfig[K]) => {
        dispatch(updateTelnyxConfigState({ [key]: value }))
    }

    const handleTestCall = async () => {
        if (!testTarget) return
        setCallStatus('Calling...')
        try {
            const res = await api.post<{ status: string, call_id?: string, detail?: string }>('/v1/calls/test-outbound', { to: testTarget })
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
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-emerald-500/10 rounded-lg">
                    <Network className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Conectividad & Hardware</h3>
                    <p className="text-xs text-slate-400">BYOC, SIP Trunking, Grabación y Compliance.</p>
                </div>
            </div>

            {/* Sub-Tabs */}
            <div className="bg-slate-900/50 border border-white/5 rounded-xl p-1 flex space-x-1">
                {[
                    { id: 'keys', label: '🔑 Credenciales', icon: null },
                    { id: 'sip', label: '📡 SIP & Trunking', icon: null },
                    { id: 'features', label: '⚙️ Opciones Llamada', icon: null }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setSubTab(tab.id as 'keys' | 'sip' | 'features')}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${subTab === tab.id
                            ? 'bg-slate-700 text-white shadow'
                            : 'text-slate-500 hover:text-slate-300'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content: Keys */}
            {subTab === 'keys' && (
                <div className="space-y-4">
                    {/* Twilio */}
                    <div className="p-4 rounded-xl border border-red-500/20 bg-slate-900/50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-5">
                            <Phone className="w-16 h-16 text-red-500" />
                        </div>
                        <h4 className="text-sm font-bold text-red-400 mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span> Twilio (Phone)
                        </h4>
                        <div className="space-y-4">
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Credentials</label>
                                <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 rounded border border-white/5">
                                    <span className="text-xs text-red-400 font-mono">🔒 Configured via Environment</span>
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">From Number</label>
                                <Input
                                    aria-label="Twilio From Number"
                                    value={twilio.twilioFromNumber}
                                    onChange={(e) => updateTwilio('twilioFromNumber', e.target.value)}
                                    placeholder="+1234567890"
                                    className="font-mono text-xs"
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
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="md:col-span-2">
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Credentials</label>
                                <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 rounded border border-white/5">
                                    <span className="text-xs text-emerald-400 font-mono">🔒 API Key via Environment</span>
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">SIP Connection ID</label>
                                <Input
                                    aria-label="SIP Connection ID"
                                    value={telnyx.telnyxConnectionId}
                                    onChange={(e) => updateTelnyx('telnyxConnectionId', e.target.value)}
                                    placeholder="Uuid"
                                    className="font-mono text-xs"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Caller ID (Override)</label>
                                <Input
                                    aria-label="Caller ID Override"
                                    value={telnyx.callerIdTelnyx}
                                    onChange={(e) => updateTelnyx('callerIdTelnyx', e.target.value)}
                                    placeholder="+1..."
                                    className="font-mono text-xs"
                                />
                            </div>

                            {/* Test Driver Widget */}
                            <div className="md:col-span-2 mt-2 pt-2 border-t border-emerald-500/20">
                                <label className="text-[10px] uppercase text-emerald-500 font-bold block mb-1">🚑 Test Driver (Real Call)</label>
                                <div className="flex gap-2">
                                    <Input
                                        aria-label="Test Call Target"
                                        value={testTarget}
                                        onChange={(e) => setTestTarget(e.target.value)}
                                        placeholder="To: +1..."
                                        className="font-mono text-xs bg-black/40"
                                    />
                                    <button
                                        onClick={handleTestCall}
                                        disabled={!testTarget}
                                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded shadow-lg transition-all flex items-center gap-1 disabled:opacity-50"
                                    >
                                        <span>📞</span> Call
                                    </button>
                                </div>
                                {callStatus && <span className="text-[10px] text-slate-400 mt-1 block">{callStatus}</span>}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Content: SIP */}
            {subTab === 'sip' && (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Twilio SIP */}
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
                            <h5 className="text-xs font-bold text-slate-300 mb-3">Twilio SIP Trunking</h5>
                            <div className="space-y-3">
                                <Input
                                    aria-label="Twilio SIP Trunk URI"
                                    label="SIP Trunk URI"
                                    value={twilio.sipTrunkUriPhone}
                                    onChange={(e) => updateTwilio('sipTrunkUriPhone', e.target.value)}
                                    placeholder="sip:..."
                                    className="text-xs"
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <Input
                                        aria-label="Twilio SIP User"
                                        placeholder="User"
                                        value={twilio.sipAuthUserPhone}
                                        onChange={(e) => updateTwilio('sipAuthUserPhone', e.target.value)}
                                        className="text-xs"
                                    />
                                    <Input
                                        aria-label="Twilio SIP Pass"
                                        type="password"
                                        placeholder="Pass"
                                        value={twilio.sipAuthPassPhone}
                                        onChange={(e) => updateTwilio('sipAuthPassPhone', e.target.value)}
                                        className="text-xs"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-slate-500 block mb-1">Geo-Region</label>
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
                            <h5 className="text-xs font-bold text-slate-300 mb-3">Telnyx SIP Trunking</h5>
                            <div className="space-y-3">
                                <Input
                                    aria-label="Telnyx SIP Trunk URI"
                                    label="SIP Trunk URI"
                                    value={telnyx.sipTrunkUriTelnyx}
                                    onChange={(e) => updateTelnyx('sipTrunkUriTelnyx', e.target.value)}
                                    placeholder="sip:..."
                                    className="text-xs"
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <Input
                                        aria-label="Telnyx SIP User"
                                        placeholder="User"
                                        value={telnyx.sipAuthUserTelnyx}
                                        onChange={(e) => updateTelnyx('sipAuthUserTelnyx', e.target.value)}
                                        className="text-xs"
                                    />
                                    <Input
                                        aria-label="Telnyx SIP Pass"
                                        type="password"
                                        placeholder="Pass"
                                        value={telnyx.sipAuthPassTelnyx}
                                        onChange={(e) => updateTelnyx('sipAuthPassTelnyx', e.target.value)}
                                        className="text-xs"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-slate-500 block mb-1">Geo-Region</label>
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
                    <div className="bg-indigo-900/20 p-3 rounded border border-indigo-500/20">
                        <label className="text-xs font-bold text-indigo-300 block mb-1">Fallback Number (Desvío de Emergencia)</label>
                        <div className="flex gap-2">
                            <Input
                                aria-label="Fallback Number"
                                value={twilio.fallbackNumberPhone}
                                onChange={(e) => updateTwilio('fallbackNumberPhone', e.target.value)}
                                placeholder="+1..."
                                className="flex-1 text-xs"
                            />
                            <span className="text-[10px] text-slate-500 self-center">Si falla el bot, desviar aquí.</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Content: Features */}
            {subTab === 'features' && (
                <div className="space-y-4">
                    {/* Recording */}
                    <div className="p-4 rounded-lg border border-white/5 bg-slate-900/40">
                        <h5 className="text-xs font-bold text-white mb-3">Grabación de Llamadas</h5>

                        {/* Twilio */}
                        <div className="flex justify-between items-center py-2 border-b border-white/5">
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-slate-300 w-24">Twilio</span>
                                <Select
                                    aria-label="Twilio Recording Channels"
                                    value={twilio.recordingChannelsPhone}
                                    onChange={(e) => updateTwilio('recordingChannelsPhone', e.target.value as 'mono' | 'dual')}
                                    className="h-8 text-[10px] w-32"
                                >
                                    <option value="mono">Mono</option>
                                    <option value="dual">Dual</option>
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
                        <div className="flex justify-between items-center py-2">
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-slate-300 w-24">Telnyx</span>
                                <Select
                                    aria-label="Telnyx Recording Channels"
                                    value={telnyx.recordingChannelsTelnyx}
                                    onChange={(e) => updateTelnyx('recordingChannelsTelnyx', e.target.value as 'mono' | 'dual')}
                                    className="h-8 text-[10px] w-32"
                                >
                                    <option value="mono">Mono</option>
                                    <option value="dual">Dual</option>
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
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-3 flex items-center gap-2">
                                <Shield className="w-4 h-4 text-blue-400" />
                                Compliance & HIPAA
                            </h5>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-slate-400">HIPAA (Twilio)</span>
                                    <input type="checkbox" aria-label="Enable Twilio HIPAA" checked={twilio.hipaaEnabledPhone} onChange={(e) => updateTwilio('hipaaEnabledPhone', e.target.checked)} />
                                </div>
                                <div className="flex justify-between items-center pt-2 border-t border-white/5">
                                    <span className="text-xs text-slate-400">HIPAA (Telnyx)</span>
                                    <input type="checkbox" aria-label="Enable Telnyx HIPAA" checked={telnyx.hipaaEnabledTelnyx} onChange={(e) => updateTelnyx('hipaaEnabledTelnyx', e.target.checked)} />
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <h5 className="text-xs font-bold text-slate-300 mb-3">Advanced Features</h5>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-slate-400">DTMF (Twilio)</span>
                                    <input type="checkbox" aria-label="Enable Twilio DTMF" checked={twilio.dtmfListeningEnabledPhone} onChange={(e) => updateTwilio('dtmfListeningEnabledPhone', e.target.checked)} />
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-slate-400">DTMF (Telnyx)</span>
                                    <input type="checkbox" aria-label="Enable Telnyx DTMF" checked={telnyx.dtmfListeningEnabledTelnyx} onChange={(e) => updateTelnyx('dtmfListeningEnabledTelnyx', e.target.checked)} />
                                </div>
                                <div className="pt-2 border-t border-white/5">
                                    <span className="text-xs text-slate-400 block mb-1">AMD (Telnyx)</span>
                                    <Select
                                        aria-label="Telnyx AMD Config"
                                        value={telnyx.amdConfig}
                                        onChange={(e) => updateTelnyx('amdConfig', e.target.value as 'disabled' | 'detect' | 'detect_hangup' | 'detect_message_end')}
                                        className="h-8 text-[10px]"
                                    >
                                        <option value="disabled">Disabled</option>
                                        <option value="detect">Detect Only</option>
                                        <option value="detect_hangup">Detect & Hangup</option>
                                        <option value="detect_message_end">Detect Message End</option>
                                    </Select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

