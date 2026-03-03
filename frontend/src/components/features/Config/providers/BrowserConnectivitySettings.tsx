import { Globe } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'

export const BrowserConnectivitySettings = () => {
    const { t } = useTranslation()

    return (
        <div className="space-y-4">
            <div className="p-8 rounded-xl border border-blue-500/20 bg-slate-900/50 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-4">
                    <Globe className="w-8 h-8 text-blue-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">{t('connectivity.browser_empty_title')}</h4>
                <p className="text-sm text-slate-400 max-w-sm">
                    {t('connectivity.browser_empty_desc')}
                </p>
            </div>
        </div>
    )
}
