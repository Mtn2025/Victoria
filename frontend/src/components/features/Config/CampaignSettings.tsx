import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Input } from '@/components/ui/Input'
import { BrowserConfig } from '@/types/config' // Using BrowserConfig generic for now
import { Megaphone, Link, Database, Upload, FileText, Loader2 } from 'lucide-react'

export const CampaignSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)
    const { activeProfile } = useAppSelector(state => state.ui)

    // In a real scenario, we'd check activeProfile or have a selector. 
    // For simplicity, we bind to browser config placeholders or similar.

    const [campaignName, setCampaignName] = useState('')
    const [campaignFile, setCampaignFile] = useState<File | null>(null)
    const [isUploading, setIsUploading] = useState(false)

    // Config Updates (Integrations)
    const update = (key: keyof BrowserConfig, value: any) => {
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

        // TODO: Implement actual API call
        // const formData = new FormData()
        // formData.append('file', campaignFile)
        // formData.append('name', campaignName)
        // await api.post('/campaigns/upload', formData)

        setTimeout(() => {
            setIsUploading(false)
            alert('Campaña iniciada (Simulación)')
            setCampaignName('')
            setCampaignFile(null)
        }, 1500)
    }

    // Simulator Warning Check
    if (activeProfile === 'browser') {
        return (
            <div className="space-y-6 animate-fade-in-up">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                        <Megaphone className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">Gestor de Campañas</h3>
                        <p className="text-xs text-slate-400">Outbound calling y automatización masiva.</p>
                    </div>
                </div>

                <div className="p-8 text-center border border-slate-700 rounded-xl bg-slate-800/50 animate-fade-in-up">
                    <p className="text-slate-400">🚫 Las campañas Outbound no están disponibles en modo Simulador.</p>
                    <p className="text-xs text-slate-500 mt-2">Por favor, conecta Twilio o Telnyx para usar esta función.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                    <Megaphone className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Gestor de Campañas</h3>
                    <p className="text-xs text-slate-400">Outbound calling y automatización masiva.</p>
                </div>
            </div>

            {/* Campaign Launcher */}
            <div className="glass-panel p-6 rounded-xl border border-blue-500/20 bg-blue-900/10 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                    <Megaphone className="w-24 h-24 text-blue-500" />
                </div>

                <div className="space-y-4 relative z-10">
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Nombre de la Campaña</label>
                        <Input
                            aria-label="Nombre de la Campaña"
                            value={campaignName}
                            onChange={(e) => setCampaignName(e.target.value)}
                            placeholder="Ej: Cobranza Enero 2025"
                        />
                    </div>

                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Archivo de Contactos (CSV)</label>
                        <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-blue-500 transition-colors cursor-pointer relative bg-slate-900/50">
                            <input
                                aria-label="Archivo de Contactos"
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            {!campaignFile ? (
                                <div className="text-slate-400">
                                    <Upload className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">Arrastra un archivo CSV aquí</p>
                                    <p className="text-xs text-slate-600 mt-1">phone, name</p>
                                </div>
                            ) : (
                                <div className="text-blue-400 font-medium flex items-center justify-center gap-2">
                                    <FileText className="w-6 h-6" />
                                    <span>{campaignFile.name}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!campaignFile || !campaignName || isUploading}
                        className={`w-full py-3 rounded-lg font-bold text-white shadow-lg transition-all flex justify-center items-center gap-2 ${!campaignFile || !campaignName || isUploading
                            ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 shadow-blue-500/30 hover:shadow-blue-500/50'
                            }`}
                    >
                        {isUploading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Procesando...
                            </>
                        ) : (
                            <>
                                <Megaphone className="w-4 h-4" />
                                Iniciar Campaña
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Integrations */}
            <div className="mt-6 pt-6 border-t border-slate-700/50 space-y-4">
                <h3 className="text-sm font-bold text-orange-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Link className="w-4 h-4" />
                    Integraciones
                </h3>

                {/* CRM */}
                <div className="flex items-center space-x-3 cursor-pointer p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                    <div className="p-2 bg-orange-500/10 rounded-full">
                        <Database className="w-4 h-4 text-orange-400" />
                    </div>
                    <div className="flex-1">
                        <span className="text-xs font-semibold text-slate-200 block">CRM Integration (Baserow)</span>
                        <span className="text-[10px] text-slate-500">Sincronizar contactos automáticamente.</span>
                    </div>
                    <input
                        type="checkbox"
                        aria-label="Enable CRM"
                        checked={browser.crmEnabled}
                        onChange={(e) => update('crmEnabled', e.target.checked)}
                        className="toggle-checkbox"
                    />
                </div>

                {/* Webhook */}
                <div className="space-y-3 p-4 bg-slate-800/20 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 text-indigo-400 mb-2">
                        <Link className="w-4 h-4" />
                        <span className="text-xs font-semibold uppercase tracking-wider">Webhook (End-of-Call)</span>
                    </div>

                    <div>
                        <Input
                            aria-label="Webhook URL"
                            label="URL"
                            value={browser.webhookUrl}
                            onChange={(e) => update('webhookUrl', e.target.value)}
                            placeholder="https://webhook.site/..."
                        />
                    </div>
                    <div>
                        <Input
                            aria-label="Webhook Secret"
                            label="Secret"
                            type="password"
                            value={browser.webhookSecret}
                            onChange={(e) => update('webhookSecret', e.target.value)}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
