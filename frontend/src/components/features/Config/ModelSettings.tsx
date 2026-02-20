import { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from "@/hooks/useRedux"
import { updateBrowserConfig, fetchLLMProviders, fetchLLMModels } from "@/store/slices/configSlice"
import { Label } from "@/components/ui/Label"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Textarea } from "@/components/ui/Textarea"
import { Card, CardContent } from "@/components/ui/Card"
import { AlertTriangle, Brain, MessageSquare, Shield } from "lucide-react"

export const ModelSettings = () => {
    const dispatch = useAppDispatch()
    const config = useAppSelector(state => state.config.browser)
    const { availableLLMProviders, availableLLMModels, isLoadingOptions } = useAppSelector(state => state.config)

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
                            // We do not reset the model synchronously because models need to be fetched first.
                            // However, we clear the model until the new ones arrive or let the backend/thunk handle default.
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

            <div className="border-t border-white/5 my-4" />

            {/* Conversation Style */}
            <div className="space-y-4">
                <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    Estilo de Conversación
                </h3>

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
            </div>

            <div className="border-t border-white/5 my-4" />

            {/* Advanced Controls */}
            <Card className="bg-purple-900/10 border-purple-500/20">
                <CardContent className="pt-6 space-y-6">
                    <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        Controles Avanzados de Inteligencia
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                    <div className="space-y-2">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={config.dynamicVarsEnabled}
                                onChange={(e) => handleChange('dynamicVarsEnabled', e.target.checked)}
                                className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm font-medium text-slate-200">Habilitar Variables Dinámicas</span>
                        </label>

                        {config.dynamicVarsEnabled && (
                            <Textarea
                                value={config.dynamicVars}
                                onChange={(e) => handleChange('dynamicVars', e.target.value)}
                                rows={3}
                                className="font-mono text-xs"
                                placeholder='{"nombre": "Juan Pérez", "empresa": "Acme Corp"}'
                            />
                        )}
                    </div>
                </CardContent>
            </Card>

            <div className="border-t border-white/5 my-4" />

            {/* Prompt Engineering */}
            <div className="space-y-4">
                <div className="space-y-2">
                    <Label className="flex justify-between">
                        <span>System Prompt</span>
                        <span className="text-xs text-blue-400">Instrucciones Madre</span>
                    </Label>
                    <Textarea
                        data-testid="input-system-prompt"
                        value={config.prompt}
                        onChange={(e) => handleChange('prompt', e.target.value)}
                        rows={6}
                        className="font-mono"
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

            {/* Safety */}
            <div className="pt-4 border-t border-white/5">
                <div className="p-4 bg-red-900/10 border border-red-500/20 rounded-lg space-y-3">
                    <h3 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
                        <Shield className="w-3 h-3" />
                        Lista Negra (Hallucination Safety)
                    </h3>
                    <Textarea
                        value={config.hallucination_blacklist}
                        onChange={(e) => handleChange('hallucination_blacklist', e.target.value)}
                        rows={2}
                        className="font-mono text-xs bg-red-950/20 border-red-500/30 placeholder-red-300/20"
                        placeholder="Palabras o frases prohibidas separadas por coma..."
                    />
                    <p className="text-[10px] text-slate-500 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        El asistente evitará generar estas palabras (Stop Sequences).
                    </p>
                </div>
            </div>

        </div>
    )
}
