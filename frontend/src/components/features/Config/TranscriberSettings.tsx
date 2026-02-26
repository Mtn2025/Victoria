import { useState, useEffect } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { BrowserConfig } from '@/types/config'
import { Accordion } from '@/components/ui/Accordion'
import { Ear, Plus, X } from 'lucide-react'
import { configService } from '@/services/configService'
import { useTranslation } from '@/i18n/I18nContext'

export const TranscriberSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    // Use browser config from store
    const { browser } = useAppSelector(state => state.config)
    const activeAgent = useAppSelector(state => state.agents.activeAgent)

    const [openSection, setOpenSection] = useState<string | null>('core')
    const [providers, setProviders] = useState<{ id: string, name: string }[]>([])

    // Muletillas input
    const [inputValue, setInputValue] = useState('')
    const [phrases, setPhrases] = useState<string[]>([])

    // Cargar frases de la DB al montar o al cambiar de agente
    useEffect(() => {
        if (browser.interruptionPhrases) {
            setPhrases(browser.interruptionPhrases.split(',').map(p => p.trim()).filter(Boolean))
        } else {
            setPhrases([])
        }
    }, [browser.interruptionPhrases, activeAgent?.agent_uuid])

    // Update global phrase string on array change
    const updatePhrasesGlobal = (newPhrases: string[]) => {
        setPhrases(newPhrases)
        update('interruptionPhrases', newPhrases.join(','))
    }

    const handleAddPhrase = () => {
        if (inputValue.trim()) {
            const newArray = [...phrases, inputValue.trim()]
            updatePhrasesGlobal(newArray)
            setInputValue('')
        }
    }

    const handleRemovePhrase = (indexToRemove: number) => {
        const newArray = phrases.filter((_, i) => i !== indexToRemove)
        updatePhrasesGlobal(newArray)
    }

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    // Load dynamic providers
    useEffect(() => {
        configService.getSTTProviders()
            .then(setProviders)
            .catch(e => console.error("Error loading STT providers", e))
    }, [])

    return (
        <div className="space-y-6 animate-fade-in-up pb-10">
            {/* Header */}
            <div className="flex justify-between items-center relative">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Ear className="w-5 h-5 text-emerald-400" />
                    {t('transcriber.title')}
                </h3>
            </div>

            {/* Main Content Areas inside Accordions */}
            <div className="space-y-4">
                {/* Core Config */}
                <Accordion
                    isOpen={openSection === 'core'}
                    onToggle={() => setOpenSection(openSection === 'core' ? null : 'core')}
                    className="border-emerald-500/30"
                    headerClassName="hover:bg-emerald-900/20"
                    title={
                        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <Ear className="w-4 h-4" />
                            {t('transcriber.core_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('transcriber.provider_label')}</label>
                            <Select
                                aria-label="Proveedor STT"
                                value={browser.sttProvider || ''}
                                onChange={(e) => update('sttProvider', e.target.value)}
                                className="w-full"
                            >
                                <option value="" disabled>{t('transcriber.provider_placeholder')}</option>
                                {providers.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </Select>
                            <p className="text-[10px] text-slate-500 mt-1">{t('transcriber.provider_desc')}</p>
                        </div>
                    </div>
                </Accordion>

                {/* VAD & ORCHESTRATION */}
                <Accordion
                    isOpen={openSection === 'vad'}
                    onToggle={() => setOpenSection(openSection === 'vad' ? null : 'vad')}
                    className="border-teal-500/30"
                    headerClassName="hover:bg-teal-900/20"
                    title={
                        <span className="text-sm font-bold text-teal-400 uppercase tracking-wider flex items-center gap-2">
                            <span className="text-lg">🔊</span> {t('transcriber.vad_title')}
                        </span>
                    }
                >
                    <div className="space-y-6 pt-2 pb-2">
                        {/* ENDPOINTING SLIDER */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <div>
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('transcriber.endpointing_label')}</label>
                                </div>
                                <span className="text-sm font-bold text-teal-400 bg-teal-950/50 px-2 py-0.5 rounded">
                                    {browser.sttSilenceTimeout || 1000} ms
                                </span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">300</span>
                                <input
                                    type="range"
                                    min="300"
                                    max="2000"
                                    step="50"
                                    value={browser.sttSilenceTimeout || 1000}
                                    onChange={(e) => update('sttSilenceTimeout', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">2000</span>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-500 px-8">
                                <span>{t('transcriber.endpointing_fast')}</span>
                                <span>{t('transcriber.endpointing_normal')}</span>
                                <span>{t('transcriber.endpointing_slow')}</span>
                            </div>
                            <p className="text-[10px] text-slate-500 pt-1">{t('transcriber.endpointing_desc')}</p>
                        </div>

                        {/* LISTA NEGRA (MULETILLAS) */}
                        <div className="space-y-2 pt-4 border-t border-white/5">
                            <div>
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">{t('transcriber.blacklist_label')}</label>
                                <p className="text-[10px] text-slate-500">{t('transcriber.blacklist_desc')}</p>
                            </div>

                            {/* Input Chips Container */}
                            <div className="bg-[#0f111a] border border-white/10 rounded-xl p-3 focus-within:border-teal-500/50 focus-within:ring-1 focus-within:ring-teal-500/50 transition-all mt-2">
                                <div className="flex flex-wrap gap-2 mb-2">
                                    {phrases.map((phrase, idx) => (
                                        <div key={idx} className="flex items-center gap-1 bg-white/5 border border-white/10 px-2 py-1 rounded-md text-[11px] text-slate-300">
                                            <span>{phrase}</span>
                                            <button
                                                onClick={() => handleRemovePhrase(idx)}
                                                className="hover:text-red-400 transition-colors ml-1"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        placeholder={t('transcriber.blacklist_placeholder')}
                                        className="bg-transparent text-[13px] text-white placeholder-slate-600 focus:outline-none flex-1 min-w-[120px]"
                                        value={inputValue}
                                        onChange={(e) => setInputValue(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault()
                                                handleAddPhrase()
                                            }
                                        }}
                                    />
                                    <button
                                        onClick={handleAddPhrase}
                                        disabled={!inputValue.trim()}
                                        className="text-teal-400 hover:text-teal-300 disabled:text-slate-600 disabled:cursor-not-allowed transition-colors"
                                    >
                                        <Plus className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </div>

                    </div>
                </Accordion>

            </div>
        </div>
    )
}
