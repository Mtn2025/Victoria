import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Accordion } from '@/components/ui/Accordion'
import { BrowserConfig } from '@/types/config'
import { Shield, Lock, LayoutGrid, Activity } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

export const SystemSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const { browser } = useAppSelector(state => state.config)
    const [openSection, setOpenSection] = useState<string | null>('limits')

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Header */}
            <div className="flex justify-between items-center relative mb-4">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <LayoutGrid className="w-5 h-5 text-slate-400" />
                    {t('system.title')}
                </h3>
            </div>

            <div className="space-y-4">
                {/* 1. Governance & Limits */}
                <Accordion
                    isOpen={openSection === 'limits'}
                    onToggle={() => setOpenSection(openSection === 'limits' ? null : 'limits')}
                    className="border-red-500/30"
                    headerClassName="hover:bg-red-900/20"
                    title={
                        <span className="text-sm font-bold text-red-400 tracking-wider uppercase flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            {t('system.accordion_limits')}
                        </span>
                    }
                >
                    <div className="space-y-6 pt-2">
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-[10px] uppercase text-slate-500 font-bold">{t('system.concurrency_label')}</label>
                                <span className="text-xs text-red-300 font-mono">{t('system.concurrency_val').replace('{{count}}', String(browser.concurrencyLimit))}</span>
                            </div>
                            <input
                                type="range"
                                aria-label="Concurrency Limit"
                                min="1" max="100" step="1"
                                value={browser.concurrencyLimit}
                                onChange={(e) => update('concurrencyLimit', parseInt(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                            />
                            <p className="text-[10px] text-slate-500 mt-2">{t('system.concurrency_desc')}</p>
                        </div>

                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-[10px] uppercase text-slate-500 font-bold">{t('system.spend_label')}</label>
                                <span className="text-xs text-green-300 font-mono">${browser.spendLimitDaily}</span>
                            </div>
                            <Input
                                type="number"
                                aria-label="Daily Spend Limit"
                                value={browser.spendLimitDaily}
                                onChange={(e) => update('spendLimitDaily', parseFloat(e.target.value))}
                                className="text-center font-mono text-xs max-w-[120px]"
                            />
                        </div>
                    </div>
                </Accordion>

                {/* 2. Environment & Privacy */}
                <Accordion
                    isOpen={openSection === 'privacy'}
                    onToggle={() => setOpenSection(openSection === 'privacy' ? null : 'privacy')}
                    className="border-blue-500/30"
                    headerClassName="hover:bg-blue-900/20"
                    title={
                        <span className="text-sm font-bold text-blue-400 tracking-wider uppercase flex items-center gap-2">
                            <Lock className="w-4 h-4" />
                            {t('system.accordion_env')}
                        </span>
                    }
                >
                    <div className="space-y-4 pt-2">
                        <div>
                            <label className="text-[10px] uppercase text-slate-500 font-bold block mb-1">{t('system.env_tag_label')}</label>
                            <Select
                                aria-label="Environment Tag"
                                value={browser.environment}
                                onChange={(e) => update('environment', e.target.value)}
                                className="text-xs"
                            >
                                <option value="development">{t('system.env_dev')}</option>
                                <option value="staging">{t('system.env_staging')}</option>
                                <option value="production">{t('system.env_prod')}</option>
                            </Select>
                        </div>

                        <div className="bg-indigo-900/10 p-3 rounded-lg border border-indigo-500/20 flex justify-between items-center">
                            <div>
                                <span className="text-xs font-bold text-indigo-300 block">{t('system.privacy_title')}</span>
                                <span className="text-[10px] text-indigo-400/60">{t('system.privacy_desc')}</span>
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
                                <span className="text-xs font-bold text-slate-300 block">{t('system.audit_title')}</span>
                                <span className="text-[10px] text-slate-500">{t('system.audit_desc')}</span>
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
                </Accordion>
            </div>

            {/* Health Status */}
            <div className="p-3 bg-green-900/10 rounded-lg border border-green-500/20 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-green-500 animate-pulse" />
                    <span className="text-xs font-bold text-green-400">{t('system.healthy_status')}</span>
                </div>
                <span className="text-[10px] font-mono text-green-600/70">/health -&gt; 200 OK</span>
            </div>
        </div>
    )
}
