import { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from "@/hooks/useRedux"
import { updateBrowserConfig, fetchLLMProviders, fetchLLMModels } from "@/store/slices/configSlice"
import { Label } from "@/components/ui/Label"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Accordion } from '@/components/ui/Accordion'
import { AlertTriangle, Brain, MessageSquare, Shield } from "lucide-react"
import TextareaAutosize from 'react-textarea-autosize'

export const ModelSettings = () => {
    const dispatch = useAppDispatch()
    const config = useAppSelector(state => state.config.browser)
    const { availableLLMProviders, availableLLMModels, isLoadingOptions } = useAppSelector(state => state.config)

    // Estado para controlar qué acordeón está abierto. 'core' por defecto.
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
                            Configuración Base (LLM & Prompt)
                        </span>
                    }
                >
                    <div className="space-y-6">
                        {/* LLM Selection */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Proveedor LLM</Label>
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
                            </div>
                            <div className="space-y-2">
                                <Label>Modelo LLM</Label>
                                <Select
                                    value={config.model}
                                    disabled={isLoadingOptions}
                                    onChange={(e) => handleChange('model', e.target.value)}
                                >
                                    <option value="" disabled>Seleccionar Modelo...</option>
                                    {availableLLMModels.map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </Select>
                            </div>
                        </div>

                        {/* Prompt Engineering */}
                        <div className="space-y-4 pt-2">
                            <div className="space-y-2">
                                <Label className="flex justify-between">
                                    <span>System Prompt</span>
                                    <span className="text-xs text-blue-400">Instrucciones Madre</span>
                                </Label>
                                <TextareaAutosize
                                    data-testid="input-system-prompt"
                                    value={config.prompt}
                                    onChange={(e) => handleChange('prompt', e.target.value)}
                                    minRows={6}
                                    maxRows={20}
                                    className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    placeholder="Eres un asistente útil..."
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <Input
                                    data-testid="input-initial-msg"
                                    label="Mensaje Inicial"
                                    value={config.msg}
                                    onChange={(e) => handleChange('msg', e.target.value)}
                                />

                                <div className="space-y-2">
                                    <Label>Modo Inicio</Label>
                                    <Select
                                        value={config.mode}
                                        onChange={(e) => handleChange('mode', e.target.value as 'speak-first' | 'listen-first')}
                                    >
                                        <option value="speak-first">Hablar Primero (Agente Saluda)</option>
                                        <option value="listen-first">Escuchar Primero (Usuario Habla)</option>
                                    </Select>
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
                            Estilo de Conversación
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Longitud de Respuesta</Label>
                            <Select
                                value={config.responseLength}
                                onChange={(e) => handleChange('responseLength', e.target.value)}
                            >
                                <option value="very_short">Muy Corta (1 frase breve)</option>
                                <option value="short">Corta (1-2 frases)</option>
                                <option value="medium">Media (2-3 frases)</option>
                                <option value="long">Larga (3-5 frases)</option>
                                <option value="detailed">Detallada (sin límite)</option>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Tono de Conversación</Label>
                            <Select
                                value={config.conversationTone}
                                onChange={(e) => handleChange('conversationTone', e.target.value)}
                            >
                                <option value="professional">Profesional</option>
                                <option value="friendly">Amigable</option>
                                <option value="warm">Cálido</option>
                                <option value="enthusiastic">Entusiasta</option>
                                <option value="neutral">Neutral</option>
                                <option value="empathetic">Empático</option>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Nivel de Formalidad</Label>
                            <Select
                                value={config.conversationFormality}
                                onChange={(e) => handleChange('conversationFormality', e.target.value)}
                            >
                                <option value="very_formal">Muy Formal</option>
                                <option value="formal">Formal</option>
                                <option value="semi_formal">Semi-Formal</option>
                                <option value="casual">Casual</option>
                                <option value="very_casual">Muy Casual</option>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Velocidad de Interacción</Label>
                            <Select
                                value={config.conversationPacing}
                                onChange={(e) => handleChange('conversationPacing', e.target.value)}
                            >
                                <option value="fast">Rápido (Interrupción rápida)</option>
                                <option value="moderate">Moderado (Equilibrado)</option>
                                <option value="relaxed">Relajado (Espera paciente)</option>
                            </Select>
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
                            Controles Avanzados de Inteligencia
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                        {/* Context Window */}
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <Label>Ventana de Contexto (Msgs)</Label>
                                <span className="text-xs text-purple-400">{config.contextWindow}</span>
                            </div>
                            <input
                                type="range"
                                aria-label="Ventana de Contexto (Msgs)"
                                min="1" max="50" step="1"
                                value={config.contextWindow}
                                onChange={(e) => handleChange('contextWindow', parseInt(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                        </div>

                        {/* Temperature */}
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <Label>Creatividad (Temperature)</Label>
                                <span className="text-xs text-purple-400">{config.temp}</span>
                            </div>
                            <input
                                type="range"
                                aria-label="Creatividad (Temperature)"
                                min="0" max="1" step="0.1"
                                value={config.temp}
                                onChange={(e) => handleChange('temp', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                        </div>

                        {/* Frequency Penalty */}
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <Label>Penalización Frecuencia</Label>
                                <span className="text-xs text-purple-400">{config.frequencyPenalty}</span>
                            </div>
                            <input
                                type="range"
                                min="0" max="2" step="0.1"
                                value={config.frequencyPenalty}
                                onChange={(e) => handleChange('frequencyPenalty', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                            <p className="text-[10px] text-slate-500">Evita repetir palabras.</p>
                        </div>

                        {/* Presence Penalty */}
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <Label>Penalización Presencia</Label>
                                <span className="text-xs text-purple-400">{config.presencePenalty}</span>
                            </div>
                            <input
                                type="range"
                                min="0" max="2" step="0.1"
                                value={config.presencePenalty}
                                onChange={(e) => handleChange('presencePenalty', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                            <p className="text-[10px] text-slate-500">Fomenta nuevos temas.</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/5 pb-2">
                        <div className="space-y-2">
                            <Label>Estrategia de Herramientas</Label>
                            <Select
                                value={config.toolChoice}
                                onChange={(e) => handleChange('toolChoice', e.target.value)}
                            >
                                <option value="auto">Automático (Decide el modelo)</option>
                                <option value="required">Obligatorio (Siempre usar)</option>
                                <option value="none">Desactivado (Nunca usar)</option>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Max Tokens</Label>
                            <Input
                                type="number"
                                value={config.tokens}
                                onChange={(e) => handleChange('tokens', parseInt(e.target.value))}
                            />
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
                            <span className="text-sm font-medium text-slate-200">Habilitar Variables Dinámicas</span>
                        </label>

                        {config.dynamicVarsEnabled && (
                            <TextareaAutosize
                                value={config.dynamicVars}
                                onChange={(e) => handleChange('dynamicVars', e.target.value)}
                                minRows={2}
                                className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                placeholder='{"nombre": "Juan Pérez", "empresa": "Acme Corp"}'
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
                            Lista Negra (Hallucination Safety)
                        </span>
                    }
                >
                    <div className="space-y-3">
                        <TextareaAutosize
                            value={config.hallucination_blacklist}
                            onChange={(e) => handleChange('hallucination_blacklist', e.target.value)}
                            minRows={2}
                            className="flex w-full rounded-lg border border-red-500/30 bg-red-950/20 px-3 py-2 text-sm text-white placeholder:text-red-300/20 focus:outline-none focus:ring-1 focus:ring-red-500"
                            placeholder="Palabras o frases prohibidas separadas por coma..."
                        />
                        <p className="text-[10px] text-slate-500 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            El asistente evitará generar estas palabras (Stop Sequences).
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
                            Finalización Autónoma (Smart Hangup)
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
                                <span className="text-sm font-medium text-slate-200">Permitir a la IA colgar la llamada</span>
                                <span className="text-[10px] text-slate-500">El Agente usará una herramienta (tool) secreta para cortar la llamada al despedirse o de ser necesario.</span>
                            </div>
                        </label>

                        {config.endCallEnabled && (
                            <div className="space-y-4 pt-2 border-t border-white/5 animate-in fade-in zoom-in duration-300">
                                <div className="space-y-2">
                                    <Label>Instrucciones de Despedida Restringida</Label>
                                    <TextareaAutosize
                                        value={config.endCallInstructions}
                                        onChange={(e) => handleChange('endCallInstructions', e.target.value)}
                                        minRows={2}
                                        className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                        placeholder="Ej: Si el cliente dice que no tiene tiempo, dile 'Gracias por tu tiempo, excelente día' y cuelga. Nunca ruegues."
                                    />
                                    <p className="text-[10px] text-slate-500">
                                        Entrena al Agente indicando bajo qué comportamientos o evasivas del lado del cliente tiene rotundo permiso de llamar a la herramienta de colgar.
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label>Keywords Force-Quit (Palabras de Emergencia)</Label>
                                    <Input
                                        value={config.endCallPhrases}
                                        onChange={(e) => handleChange('endCallPhrases', e.target.value)}
                                        placeholder="adiós, bye, hasta luego, no me interesa"
                                    />
                                    <p className="text-[10px] text-slate-500 flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" />
                                        (Opcional) Si la IA pronuncia estas frases al final de su turno, el Call Engine cerrará abruptamente la sesión. Sepáralas con comas.
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
