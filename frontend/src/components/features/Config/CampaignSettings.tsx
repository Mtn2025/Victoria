import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Input } from '@/components/ui/Input'
import { BrowserConfig } from '@/types/config'
import { Accordion } from '@/components/ui/Accordion'
import { Megaphone, Link, Database, Upload, FileText, Loader2 } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

export const CampaignSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const { browser } = useAppSelector(state => state.config)

    const [openSection, setOpenSection] = useState<string | null>('launcher')

    const [campaignName, setCampaignName] = useState('')
    const [campaignFile, setCampaignFile] = useState<File | null>(null)
    const [isUploading, setIsUploading] = useState(false)

    // Config Updates (Integrations)
    const update = <K extends keyof BrowserConfig>(key: K, value: BrowserConfig[K]) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setCampaignFile(e.target.files[0])
        }
    }

    const handleUpload = async () => {
        if (!campaignFile || !campaignName) return
        setIsUploading(true)

        // Simulación de carga...
        setTimeout(() => {
            setIsUploading(false)
            alert(t('campaigns.success_toast'))
            setCampaignName('')
            setCampaignFile(null)
        }, 1500)
    }

    // La UI ya bloquea este tab en el Sidebar gracias a `isTelephonyOnly = true`.

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Header */}
            <div className="flex justify-between items-center relative mb-4">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Megaphone className="w-5 h-5 text-blue-400" />
                    {t('campaigns.title')}
                </h3>
            </div>

            {/* Campaign Launcher */}
            <Accordion
                isOpen={openSection === 'launcher'}
                onToggle={() => setOpenSection(openSection === 'launcher' ? null : 'launcher')}
                className="border-blue-500/30"
                headerClassName="hover:bg-blue-900/20"
                title={
                    <span className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                        <Megaphone className="w-4 h-4" />
                        {t('campaigns.accordion_launcher')}
                    </span>
                }
            >
                <div className="space-y-6">
                    <div>
                        <Input
                            aria-label="Nombre de la Campaña"
                            label={t('campaigns.name_label')}
                            value={campaignName}
                            onChange={(e) => setCampaignName(e.target.value)}
                            placeholder={t('campaigns.name_placeholder')}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">{t('campaigns.csv_label')}</label>
                        <div className="border-2 border-dashed border-slate-700/80 rounded-xl p-8 text-center hover:border-blue-500/50 hover:bg-slate-800/30 transition-all cursor-pointer relative bg-[#0f111a]">
                            <input
                                aria-label="Archivo de Contactos"
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            {!campaignFile ? (
                                <div className="text-slate-400">
                                    <Upload className="w-8 h-8 mx-auto mb-3 opacity-60 text-blue-400" />
                                    <p className="text-[13px] font-medium text-slate-300">{t('campaigns.csv_drop')}</p>
                                    <p className="text-[10px] text-slate-500 mt-2">{t('campaigns.csv_cols')}</p>
                                </div>
                            ) : (
                                <div className="text-blue-400 font-medium flex flex-col items-center justify-center gap-2">
                                    <FileText className="w-8 h-8 mb-2" />
                                    <span className="text-sm">{campaignFile.name}</span>
                                    <span className="text-[10px] text-slate-500 mt-1">Archivo listo para subir</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!campaignFile || !campaignName || isUploading}
                        className={`w-full py-3 rounded-xl font-bold text-white shadow-lg transition-all flex justify-center items-center gap-2 ${!campaignFile || !campaignName || isUploading
                            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 shadow-blue-500/20 hover:shadow-blue-500/40 hover:scale-[1.01]'
                            }`}
                    >
                        {isUploading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                {t('campaigns.processing')}
                            </>
                        ) : (
                            <>
                                <Megaphone className="w-4 h-4" />
                                {t('campaigns.start_btn')}
                            </>
                        )}
                    </button>
                </div>
            </Accordion>

            {/* Integrations */}
            <Accordion
                isOpen={openSection === 'integrations'}
                onToggle={() => setOpenSection(openSection === 'integrations' ? null : 'integrations')}
                className="border-orange-500/30"
                headerClassName="hover:bg-orange-900/20"
                title={
                    <span className="text-sm font-bold text-orange-400 uppercase tracking-wider flex items-center gap-2">
                        <Link className="w-4 h-4" />
                        {t('campaigns.accordion_integrations')}
                    </span>
                }
            >
                <div className="space-y-4">
                    {/* CRM */}
                    <label className={`flex items-center justify-between p-4 cursor-pointer rounded-xl border transition-all duration-200 ${browser.crmEnabled ? 'border-orange-500/30 bg-orange-900/20' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'}`}>
                        <div className="flex gap-4 items-center">
                            <div className={`p-3 rounded-full transition-colors ${browser.crmEnabled ? 'bg-orange-500/30' : 'bg-orange-500/10'}`}>
                                <Database className={`w-5 h-5 ${browser.crmEnabled ? 'text-orange-400' : 'text-orange-500/50'}`} />
                            </div>
                            <div>
                                <span className="text-sm font-bold text-white block">{t('campaigns.crm_label')}</span>
                                <span className="text-xs text-slate-400 mt-1 block">{t('campaigns.crm_desc')}</span>
                            </div>
                        </div>
                        <div className="flex items-center h-5">
                            <input
                                type="checkbox"
                                className="toggle-checkbox"
                                checked={browser.crmEnabled}
                                onChange={(e) => update('crmEnabled', e.target.checked)}
                            />
                        </div>
                    </label>

                    {/* Webhook */}
                    <div className="mt-4 p-5 bg-slate-900/30 rounded-xl border border-slate-800/50 space-y-4">
                        <div className="flex items-center gap-2 text-indigo-400 mb-2">
                            <Link className="w-4 h-4" />
                            <span className="text-xs font-bold uppercase tracking-wider">{t('campaigns.webhook_title')}</span>
                        </div>

                        <div>
                            <Input
                                aria-label="Webhook URL"
                                label={t('campaigns.webhook_url_label')}
                                value={browser.webhookUrl}
                                onChange={(e) => update('webhookUrl', e.target.value)}
                                placeholder={t('campaigns.webhook_url_placeholder')}
                                className="bg-slate-900 border-l-2 border-l-indigo-500/50 text-xs font-mono"
                                autoComplete="off"
                            />
                            <p className="text-[10px] text-slate-500 mt-2">{t('campaigns.webhook_desc')}</p>
                        </div>
                        <div>
                            <Input
                                aria-label="Webhook Secret"
                                label={t('campaigns.webhook_secret_label')}
                                type="password"
                                value={browser.webhookSecret}
                                onChange={(e) => update('webhookSecret', e.target.value)}
                                placeholder={t('campaigns.webhook_secret_placeholder')}
                                className="bg-slate-900 text-xs font-mono"
                                autoComplete="new-password"
                            />
                        </div>
                    </div>
                </div>
            </Accordion>
        </div>
    )
}
