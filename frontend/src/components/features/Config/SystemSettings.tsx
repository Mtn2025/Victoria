import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { BrowserConfig } from '@/types/config'
import { Shield, Lock, LayoutGrid, Activity } from 'lucide-react'

export const SystemSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-slate-500/10 rounded-lg">
                    <LayoutGrid className="w-5 h-5 text-slate-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Sistema & Gobierno</h3>
                    <p className="text-xs text-slate-400">Infraestructura, seguridad y límites.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* 1. Governance & Limits */}
                <div className="glass-panel p-5 rounded-xl border border-white/5 relative bg-slate-900/50">
                    <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <Shield className="w-4 h-4 text-red-400" />
                        Límites de Seguridad
                    </h4>

                    <div className="space-y-6">
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-[10px] uppercase text-slate-500 font-bold">Concurrency Limit</label>
                                <span className="text-xs text-red-300 font-mono">{browser.concurrencyLimit} calls</span>
                            </div>
                            <input
                                type="range"
                                aria-label="Concurrency Limit"
                                min="1" max="100" step="1"
                                value={browser.concurrencyLimit}
                                onChange={(e) => update('concurrencyLimit', parseInt(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                            />
                            <p className="text-[10px] text-slate-500 mt-1">Máximo de llamadas simultáneas activas.</p>
                        </div>

                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-[10px] uppercase text-slate-500 font-bold">Daily Spend Limit ($)</label>
                                <span className="text-xs text-green-300 font-mono">${browser.spendLimitDaily}</span>
                            </div>
                            <Input
                                type="number"
                                aria-label="Daily Spend Limit"
                                value={browser.spendLimitDaily}
                                onChange={(e) => update('spendLimitDaily', parseFloat(e.target.value))}
                                className="text-center font-mono text-xs"
                            />
                        </div>
                    </div>
                </div>

                {/* 2. Environment & Privacy */}
                <div className="glass-panel p-5 rounded-xl border border-white/5 relative bg-slate-900/50">
                    <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <Lock className="w-4 h-4 text-blue-400" />
                        Entorno & Privacidad
                    </h4>

                    <div className="space-y-4">
                        <div>
                            <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Environment Tag</label>
                            <Select
                                aria-label="Environment Tag"
                                value={browser.environment}
                                onChange={(e) => update('environment', e.target.value)}
                            >
                                <option value="development">Development (Sandbox)</option>
                                <option value="staging">Staging (Pre-Prod)</option>
                                <option value="production">Production (Live)</option>
                            </Select>
                        </div>

                        <div className="bg-indigo-900/10 p-3 rounded-lg border border-indigo-500/20 flex justify-between items-center">
                            <div>
                                <span className="text-xs font-bold text-indigo-300 block">Privacy Mode</span>
                                <span className="text-[10px] text-indigo-400/60">No usar data para entrenamiento.</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Privacy Mode"
                                checked={browser.privacyMode}
                                onChange={(e) => update('privacyMode', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>

                        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex justify-between items-center">
                            <div>
                                <span className="text-xs font-bold text-slate-300 block">Audit Logs</span>
                                <span className="text-[10px] text-slate-500">Registrar cambios de configuración.</span>
                            </div>
                            <input
                                type="checkbox"
                                aria-label="Audit Logs"
                                checked={browser.auditLogEnabled}
                                onChange={(e) => update('auditLogEnabled', e.target.checked)}
                                className="toggle-checkbox"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Health Status */}
            <div className="p-3 bg-green-900/10 rounded-lg border border-green-500/20 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-green-500 animate-pulse" />
                    <span className="text-xs font-bold text-green-400">System Healthy</span>
                </div>
                <span className="text-[10px] font-mono text-green-600/70">/health -&gt; 200 OK</span>
            </div>
        </div>
    )
}
