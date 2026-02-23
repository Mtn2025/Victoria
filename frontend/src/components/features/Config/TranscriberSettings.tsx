import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { BrowserConfig } from '@/types/config'
import { Accordion } from '@/components/ui/Accordion'
import { Ear } from 'lucide-react'

export const TranscriberSettings = () => {
    const dispatch = useAppDispatch()
    // Use browser config from store
    const { browser } = useAppSelector(state => state.config)

    const [openSection, setOpenSection] = useState<string | null>('core')

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
                <Ear className="w-5 h-5 text-emerald-400" />
                Configuración de Transcripción (STT)
            </h3>

            {/* Main Content Areas inside Accordions */}
            <div className="space-y-3">
                {/* Core Config */}
                <Accordion
                    isOpen={openSection === 'core'}
                    onToggle={() => setOpenSection(openSection === 'core' ? null : 'core')}
                    className="border-emerald-500/30"
                    headerClassName="hover:bg-emerald-900/20"
                    title={
                        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <Ear className="w-4 h-4" />
                            Configuración Base (Motor STT)
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Proveedor STT</label>
                            <Select
                                aria-label="Proveedor STT"
                                value={browser.sttProvider}
                                onChange={(e) => update('sttProvider', e.target.value)}
                            >
                                <option value="azure">Azure Speech</option>
                            </Select>
                            <p className="text-[10px] text-slate-500 mt-1">El idioma de transcripción (ej. es-MX) se hereda automáticamente de la Configuración Base del Agente.</p>
                        </div>
                    </div>
                </Accordion>
            </div>
        </div>
    )
}
