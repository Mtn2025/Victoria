import { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from "@/hooks/useRedux"
import { updateBrowserConfig, fetchLLMProviders, fetchLLMModels } from "@/store/slices/configSlice"
import { Label } from "@/components/ui/Label"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Accordion } from '@/components/ui/Accordion'
import { AlertTriangle, Brain, MessageSquare, Shield } from "lucide-react"
import TextareaAutosize from 'react-textarea-autosize'
import { useTranslation } from '@/i18n/I18nContext'

export const ModelSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const config = useAppSelector(state => state.config.browser)
    const { availableLLMProviders, availableLLMModels, isLoadingOptions } = useAppSelector(state => state.config)

    const [openSection, setOpenSection] = useState<string | null>('core')

    useEffect(() => {
        if (availableLLMProviders.length === 0) {
            dispatch(fetchLLMProviders())
        }
    }, [dispatch, availableLLMProviders.length])

    useEffect(() => {
        if (config.provider) {
            dispatch(fetchLLMModels(config.provider))
        }
    }, [dispatch, config.provider])

    const handleChange = <K extends keyof typeof config>(field: K, value: typeof config[K]) => {
        dispatch(updateBrowserConfig({ [field]: value }))
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* AI Control Accordions */}
            <div className="space-y-3">
                {/* Core Config */}
                <Accordion
                    isOpen={openSection === 'core'}
                    onToggle={() => setOpenSection(openSection === 'core' ? null : 'core')}
                    className="border-blue-500/30"
                    headerClassName="hover:bg-blue-900/20"
                    title={
                        <span className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                            <Brain className="w-4 h-4" />
                            {t('model.core_title')}
                        </span>
                    }
                >
                    <div className="space-y-6">
                        {/* LLM Selection */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>{t('model.provider_label')}</Label>
                                <Select
                                    value={config.provider}
                                    disabled={isLoadingOptions}
                                    onChange={(e) => {
                                        const newProvider = e.target.value
                                        handleChange('provider', newProvider)
                                        handleChange('model', '')
                                    }}
                                >
                                    {availableLLMProviders.map(p => (
                                        <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                </Select>
                                <p className="text-[10px] text-slate-500">{t('model.provider_desc')}</p>
                            </div>
                            <div className="space-y-2">
                                <Label>{t('model.model_label')}</Label>
                                <Select
                                    value={config.model}
                                    disabled={isLoadingOptions}
                                    onChange={(e) => handleChange('model', e.target.value)}
                                >
                                    <option value="" disabled>{t('model.model_placeholder')}</option>
                                    {availableLLMModels.map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </Select>
                                <p className="text-[10px] text-slate-500">{t('model.model_desc')}</p>
                            </div>
                        </div>

                        {/* Prompt Engineering */}
                        <div className="space-y-4 pt-2">
                            <div className="space-y-2">
                                <Label className="flex justify-between">
                                    <span>{t('model.system_prompt_label')}</span>
                                    <span className="text-xs text-blue-400 font-medium px-2 py-0.5 bg-blue-500/10 rounded-full">{t('model.system_prompt_badge')}</span>
                                </Label>
                                <TextareaAutosize
                                    data-testid="input-system-prompt"
                                    value={config.prompt}
                                    onChange={(e) => handleChange('prompt', e.target.value)}
                                    minRows={6}
                                    maxRows={20}
                                    className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    placeholder={t('model.system_prompt_placeholder')}
                                />
                                <p className="text-[10px] text-slate-500">{t('model.system_prompt_desc')}</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>{t('model.initial_msg_label')}</Label>
                                    <Input
                                        data-testid="input-initial-msg"
                                        value={config.msg}
                                        onChange={(e) => handleChange('msg', e.target.value)}
                                    />
                                    <p className="text-[10px] text-slate-500">{t('model.initial_msg_desc')}</p>
                                </div>

                                <div className="space-y-2">
                                    <Label>{t('model.start_mode_label')}</Label>
                                    <Select
                                        value={config.startMode}
                                        onChange={(e) => handleChange('startMode', e.target.value as 'speak-first' | 'listen-first')}
                                    >
                                        <option value="speak-first">{t('model.start_mode_speak')}</option>
                                        <option value="listen-first">{t('model.start_mode_listen')}</option>
                                    </Select>
                                    <p className="text-[10px] text-slate-500">{t('model.start_mode_desc')}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </Accordion>

                {/* Conversation Style */}
                <Accordion
                    isOpen={openSection === 'style'}
                    onToggle={() => setOpenSection(openSection === 'style' ? null : 'style')}
                    title={
                        <span className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            {t('model.style_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>{t('model.response_length_label')}</Label>
                            <Select
                                value={config.responseLength}
                                onChange={(e) => handleChange('responseLength', e.target.value)}
                            >
                                <option value="very_short">{t('model.rl_very_short')}</option>
                                <option value="short">{t('model.rl_short')}</option>
                                <option value="medium">{t('model.rl_medium')}</option>
                                <option value="long">{t('model.rl_long')}</option>
                                <option value="detailed">{t('model.rl_detailed')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('model.response_length_desc')}</p>
                        </div>

                        <div className="space-y-2">
                            <Label>{t('model.tone_label')}</Label>
                            <Select
                                value={config.conversationTone}
                                onChange={(e) => handleChange('conversationTone', e.target.value)}
                            >
                                <option value="professional">{t('model.tone_professional')}</option>
                                <option value="friendly">{t('model.tone_friendly')}</option>
                                <option value="warm">{t('model.tone_warm')}</option>
                                <option value="enthusiastic">{t('model.tone_enthusiastic')}</option>
                                <option value="neutral">{t('model.tone_neutral')}</option>
                                <option value="empathetic">{t('model.tone_empathetic')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('model.tone_desc')}</p>
                        </div>

                        <div className="space-y-2">
                            <Label>{t('model.formality_label')}</Label>
                            <Select
                                value={config.conversationFormality}
                                onChange={(e) => handleChange('conversationFormality', e.target.value)}
                            >
                                <option value="very_formal">{t('model.formality_very_formal')}</option>
                                <option value="formal">{t('model.formality_formal')}</option>
                                <option value="semi_formal">{t('model.formality_semi_formal')}</option>
                                <option value="casual">{t('model.formality_casual')}</option>
                                <option value="very_casual">{t('model.formality_very_casual')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('model.formality_desc')}</p>
                        </div>

                        <div className="space-y-2">
                            <Label>{t('model.pacing_label')}</Label>
                            <Select
                                value={config.conversationPacing}
                                onChange={(e) => handleChange('conversationPacing', e.target.value)}
                            >
                                <option value="fast">{t('model.pacing_fast')}</option>
                                <option value="moderate">{t('model.pacing_moderate')}</option>
                                <option value="relaxed">{t('model.pacing_relaxed')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('model.pacing_desc')}</p>
                        </div>
                    </div>
                </Accordion>

                {/* Advanced Controls */}
                <Accordion
                    isOpen={openSection === 'advanced'}
                    onToggle={() => setOpenSection(openSection === 'advanced' ? null : 'advanced')}
                    className="border-purple-500/30"
                    headerClassName="hover:bg-purple-900/20"
                    title={
                        <span className="text-sm font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                            <Brain className="w-4 h-4" />
                            {t('model.adv_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                        {/* Context Window */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <Label>{t('model.context_window_label')}</Label>
                                <span className="text-sm font-bold text-purple-400">{config.contextWindow}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">1</span>
                                <input
                                    type="range"
                                    min="1" max="50" step="1"
                                    value={config.contextWindow}
                                    onChange={(e) => handleChange('contextWindow', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">50</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('model.context_window_desc')}</p>
                        </div>

                        {/* Temperature */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <Label>{t('model.creativity_label')}</Label>
                                <span className="text-sm font-bold text-purple-400">{config.temp}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0.0</span>
                                <input
                                    type="range"
                                    min="0" max="1" step="0.1"
                                    value={config.temp}
                                    onChange={(e) => handleChange('temp', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">1.0</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('model.creativity_desc')}</p>
                        </div>

                        {/* Frequency Penalty */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <Label>{t('model.frequency_penalty_label')}</Label>
                                <span className="text-sm font-bold text-purple-400">{config.frequencyPenalty}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0.0</span>
                                <input
                                    type="range"
                                    min="0" max="2" step="0.1"
                                    value={config.frequencyPenalty}
                                    onChange={(e) => handleChange('frequencyPenalty', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">2.0</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('model.frequency_penalty_desc')}</p>
                        </div>

                        {/* Presence Penalty */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <Label>{t('model.presence_penalty_label')}</Label>
                                <span className="text-sm font-bold text-purple-400">{config.presencePenalty}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0.0</span>
                                <input
                                    type="range"
                                    min="0" max="2" step="0.1"
                                    value={config.presencePenalty}
                                    onChange={(e) => handleChange('presencePenalty', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">2.0</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('model.presence_penalty_desc')}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/5 pb-2">
                        <div className="space-y-2">
                            <Label>{t('model.tool_strategy_label')}</Label>
                            <Select
                                value={config.toolChoice}
                                onChange={(e) => handleChange('toolChoice', e.target.value)}
                            >
                                <option value="auto">{t('model.tool_auto')}</option>
                                <option value="required">{t('model.tool_required')}</option>
                                <option value="none">{t('model.tool_none')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('model.tool_strategy_desc')}</p>
                        </div>
                        <div className="space-y-2">
                            <Label>{t('model.max_tokens_label')}</Label>
                            <Input
                                type="number"
                                value={config.tokens}
                                onChange={(e) => handleChange('tokens', parseInt(e.target.value))}
                            />
                            <p className="text-[10px] text-slate-500">{t('model.max_tokens_desc')}</p>
                        </div>
                    </div>

                    {/* Dynamic Vars */}
                    <div className="space-y-2 pt-4 border-t border-white/5">
                        <label className="flex items-center space-x-2 cursor-pointer mb-2">
                            <input
                                type="checkbox"
                                checked={config.dynamicVarsEnabled}
                                onChange={(e) => handleChange('dynamicVarsEnabled', e.target.checked)}
                                className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm font-medium text-slate-200">{t('model.dynamic_vars_enabled')}</span>
                        </label>
                        <p className="text-[10px] text-slate-500 mb-2">{t('model.dynamic_vars_desc')}</p>

                        {config.dynamicVarsEnabled && (
                            <TextareaAutosize
                                value={config.dynamicVars}
                                onChange={(e) => handleChange('dynamicVars', e.target.value)}
                                minRows={2}
                                className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                placeholder={t('model.dynamic_vars_placeholder')}
                            />
                        )}
                    </div>
                </Accordion>

                {/* Safety */}
                <Accordion
                    isOpen={openSection === 'safety'}
                    onToggle={() => setOpenSection(openSection === 'safety' ? null : 'safety')}
                    className="border-red-500/30"
                    headerClassName="hover:bg-red-900/20"
                    title={
                        <span className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
                            <Shield className="w-3 h-3" />
                            {t('model.safety_title')}
                        </span>
                    }
                >
                    <div className="space-y-3">
                        <TextareaAutosize
                            value={config.hallucination_blacklist}
                            onChange={(e) => handleChange('hallucination_blacklist', e.target.value)}
                            minRows={2}
                            className="flex w-full rounded-lg border border-red-500/30 bg-red-950/20 px-3 py-2 text-sm text-white placeholder:text-red-300/20 focus:outline-none focus:ring-1 focus:ring-red-500"
                            placeholder={t('model.blacklist_placeholder')}
                        />
                        <p className="text-[10px] text-slate-500 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 shrink-0" />
                            {t('model.blacklist_desc')}
                        </p>
                    </div>
                </Accordion>

                {/* Smart Hangup */}
                <Accordion
                    isOpen={openSection === 'hangup'}
                    onToggle={() => setOpenSection(openSection === 'hangup' ? null : 'hangup')}
                    className="border-emerald-500/30"
                    headerClassName="hover:bg-emerald-900/20"
                    title={
                        <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <Shield className="w-3 h-3" />
                            {t('model.hangup_title')}
                        </span>
                    }
                >
                    <div className="space-y-4">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={config.endCallEnabled}
                                onChange={(e) => handleChange('endCallEnabled', e.target.checked)}
                                className="w-4 h-4 rounded bg-slate-700 border-slate-600 focus:ring-emerald-500 text-emerald-600"
                            />
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-slate-200">{t('model.hangup_enabled')}</span>
                                <span className="text-[10px] text-slate-500">{t('model.hangup_enabled_desc')}</span>
                            </div>
                        </label>

                        {config.endCallEnabled && (
                            <div className="space-y-4 pt-2 border-t border-white/5 animate-in fade-in zoom-in duration-300">
                                <div className="space-y-2">
                                    <Label>{t('model.hangup_instructions_label')}</Label>
                                    <TextareaAutosize
                                        value={config.endCallInstructions}
                                        onChange={(e) => handleChange('endCallInstructions', e.target.value)}
                                        minRows={2}
                                        className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                        placeholder={t('model.hangup_instructions_placeholder')}
                                    />
                                    <p className="text-[10px] text-slate-500">
                                        {t('model.hangup_instructions_desc')}
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label>{t('model.hangup_keywords_label')}</Label>
                                    <Input
                                        value={config.endCallPhrases}
                                        onChange={(e) => handleChange('endCallPhrases', e.target.value)}
                                        placeholder={t('model.hangup_keywords_placeholder')}
                                    />
                                    <p className="text-[10px] text-slate-500 flex items-start gap-1">
                                        <AlertTriangle className="w-3 h-3 shrink-0" />
                                        {t('model.hangup_keywords_desc')}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </Accordion>
            </div>

        </div>
    )
}
