/**
 * AgentsPanel.tsx
 * Main view for agent management: list, create, activate.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { fetchAgents, fetchActiveAgent, createAgent, activateAgent } from '@/store/slices/agentsSlice'
import { Bot, Plus, Settings, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'
import { Agent } from '@/types/config'

export const AgentsPanel = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const { agents, loading, error } = useAppSelector(s => s.agents)

    const [showModal, setShowModal] = useState(false)
    const [newAgentName, setNewAgentName] = useState('')
    const [creating, setCreating] = useState(false)

    useEffect(() => {
        dispatch(fetchAgents())
        dispatch(fetchActiveAgent())
    }, [dispatch])

    const handleActivate = async (agent: Agent) => {
        await dispatch(activateAgent(agent.agent_uuid))
        // Refresh the active agent in Redux — ConfigPage's useEffect will detect
        // the new activeAgent and call fetchAgentConfig() automatically.
        dispatch(fetchActiveAgent())
    }

    const handleConfigure = (agent: Agent) => {
        if (!agent.is_active) {
            dispatch(activateAgent(agent.agent_uuid)).then(() => {
                dispatch(fetchActiveAgent())
                navigate('/config')
            })
        } else {
            navigate('/config')
        }
    }

    const handleCreate = async () => {
        if (!newAgentName.trim()) return
        setCreating(true)
        await dispatch(createAgent(newAgentName.trim()))
        setCreating(false)
        setNewAgentName('')
        setShowModal(false)
    }

    return (
        <div className="flex flex-col h-full w-full">
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-slate-900/50 backdrop-blur shrink-0">
                <div className="flex items-center gap-2">
                    <Bot size={18} className="text-blue-400" />
                    <h2 className="text-sm font-bold text-slate-100 tracking-wide uppercase">Agentes</h2>
                </div>
                <Button variant="primary" onClick={() => setShowModal(true)} className="flex items-center gap-1.5 text-xs px-3 py-1.5">
                    <Plus size={14} />
                    Nuevo Agente
                </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-3">
                {error && (
                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-400/10 border border-red-400/20 p-3 rounded-lg">
                        <AlertCircle size={14} />
                        {error}
                    </div>
                )}

                {loading && agents.length === 0 && (
                    <div className="flex items-center justify-center py-20 text-slate-500">
                        <Loader2 size={20} className="animate-spin mr-2" />
                        Cargando agentes...
                    </div>
                )}

                {!loading && agents.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-3">
                        <Bot size={40} className="opacity-30" />
                        <p className="text-sm">No hay agentes registrados.</p>
                        <Button variant="primary" onClick={() => setShowModal(true)} className="text-xs">
                            Crear primer agente
                        </Button>
                    </div>
                )}

                {agents.map((agent) => (
                    <div
                        key={agent.agent_uuid}
                        className={cn(
                            "flex items-center justify-between p-4 rounded-xl border transition-all",
                            agent.is_active
                                ? "bg-blue-900/20 border-blue-500/40 ring-1 ring-blue-500/20"
                                : "bg-slate-800/50 border-slate-700/50 hover:border-slate-600"
                        )}
                    >
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center",
                                agent.is_active ? "bg-blue-600" : "bg-slate-700"
                            )}>
                                <Bot size={16} className="text-white" />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                                    {agent.name}
                                    {agent.is_active && (
                                        <span className="text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/30 px-1.5 py-0.5 rounded-full">
                                            ACTIVO
                                        </span>
                                    )}
                                </p>
                                <p className="text-xs text-slate-500 mt-0.5">
                                    {new Date(agent.created_at).toLocaleDateString('es-MX')}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {!agent.is_active && (
                                <button
                                    onClick={() => handleActivate(agent)}
                                    disabled={loading}
                                    className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-blue-600 hover:text-white transition-all disabled:opacity-50"
                                >
                                    Activar
                                </button>
                            )}
                            <button
                                onClick={() => handleConfigure(agent)}
                                title="Configurar"
                                className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-all"
                            >
                                <Settings size={14} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Create Agent Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-80 shadow-2xl">
                        <h3 className="text-sm font-bold text-slate-100 mb-4 flex items-center gap-2">
                            <Bot size={16} className="text-blue-400" />
                            Nuevo Agente
                        </h3>
                        <input
                            type="text"
                            value={newAgentName}
                            onChange={e => setNewAgentName(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleCreate()}
                            placeholder="Nombre del agente..."
                            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-blue-500 mb-4"
                            autoFocus
                        />
                        <div className="flex gap-2">
                            <button
                                onClick={() => { setShowModal(false); setNewAgentName('') }}
                                className="flex-1 text-xs py-2 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 transition-all"
                            >
                                Cancelar
                            </button>
                            <Button
                                variant="primary"
                                onClick={handleCreate}
                                disabled={creating || !newAgentName.trim()}
                                className="flex-1 text-xs"
                            >
                                {creating ? <Loader2 size={12} className="animate-spin" /> : 'Crear'}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
