import { useAppSelector } from '@/hooks/useRedux'
import { Network } from 'lucide-react'
import { useTranslation } from '@/i18n/I18nContext'
import { TwilioConnectivitySettings } from './providers/TwilioConnectivitySettings'
import { TelnyxConnectivitySettings } from './providers/TelnyxConnectivitySettings'
import { BrowserConnectivitySettings } from './providers/BrowserConnectivitySettings'

export const ConnectivitySettings = () => {
    const { t } = useTranslation()
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    const renderProviderSettings = () => {
        switch (activeProfile) {
            case 'twilio':
                return <TwilioConnectivitySettings />
            case 'telnyx':
                return <TelnyxConnectivitySettings />
            case 'browser':
            default:
                return <BrowserConnectivitySettings />
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

            {/* Injected Provider Component */}
            {renderProviderSettings()}
        </div>
    )
}
