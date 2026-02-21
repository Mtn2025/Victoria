/**
 * AgentsPanel.tsx
 * Main view for agent management: list, create, activate, rename, delete.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import {
    fetchAgents,
    fetchActiveAgent,
    createAgent,
    activateAgent,
    updateAgentName,
    deleteAgent,
} from '@/store/slices/agentsSlice'
import { Bot, Plus, Settings, Loader2, AlertCircle, Trash2, Pencil, ArrowRight, X } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'
import { Agent } from '@/types/config'

// --------------------------------------------------------------------- //
// Manage Agent Modal                                                      //
// --------------------------------------------------------------------- //
interface ManageModalProps {
    agent: Agent
    onClose: () => void
    onConfigure: (agent: Agent) => void
}

const ManageModal = ({ agent, onClose, onConfigure }: ManageModalProps) => {
    const dispatch = useAppDispatch()
    const [name, setName] = useState(agent.name)
    const [saving, setSaving] = useState(false)
    const [confirmDelete, setConfirmDelete] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [nameError, setNameError] = useState('')

    const handleSaveName = async () => {
        if (!name.trim()) { setNameError('El nombre no puede estar vacío'); return }
        if (name.trim() === agent.name) { onClose(); return }
        setSaving(true)
        await dispatch(updateAgentName({ agentUuid: agent.agent_uuid, name: name.trim() }))
        setSaving(false)
        onClose()
    }

    const handleDelete = async () => {
        setDeleting(true)
        const result = await dispatch(deleteAgent(agent.agent_uuid))
        setDeleting(false)
        if ((result as any).error) {
            setConfirmDelete(false)
        } else {
            onClose()
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-96 shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-5">
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        <Settings size={15} className="text-blue-400" />
                        Gestionar agente
                    </h3>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
                        <X size={16} />
                    </button>
                </div>

                {/* Name field */}
                <label className="block text-xs text-slate-400 mb-1.5">Nombre</label>
                <div className="flex gap-2 mb-1">
                    <input
                        type="text"
                        value={name}
                        onChange={e => { setName(e.target.value); setNameError('') }}
                        onKeyDown={e => e.key === 'Enter' && handleSaveName()}
                        className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-blue-500"
                    />
                    <Button
                        variant="primary"
                        onClick={handleSaveName}
                        disabled={saving}
                        className="text-xs px-3"
                    >
                        {saving ? <Loader2 size={12} className="animate-spin" /> : <Pencil size={12} />}
                    </Button>
                </div>
                {nameError && <p className="text-xs text-red-400 mb-3">{nameError}</p>}

                {/* Divider */}
                <div className="border-t border-slate-700/60 my-4" />

                {/* Action: Go to Config */}
                <Button
                    variant="primary"
                    onClick={() => onConfigure(agent)}
                    className="w-full flex items-center justify-center gap-2 text-sm mb-3"
                >
                    <ArrowRight size={14} />
                    Configurar agente
                </Button>

                {/* Action: Delete */}
                {!confirmDelete ? (
                    <button
                        onClick={() => setConfirmDelete(true)}
                        disabled={agent.is_active}
                        title={agent.is_active ? 'No puedes eliminar el agente activo' : 'Eliminar agente'}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 text-xs py-2 rounded-lg transition-all",
                            agent.is_active
                                ? "bg-slate-800/50 text-slate-600 cursor-not-allowed"
                                : "bg-red-900/20 text-red-400 hover:bg-red-900/40 border border-red-900/30"
                        )}
                    >
                        <Trash2 size={12} />
                        {agent.is_active ? 'No se puede eliminar el agente activo' : 'Eliminar agente'}
                    </button>
                ) : (
                    <div className="bg-red-900/20 border border-red-900/40 rounded-lg p-3">
                        <p className="text-xs text-red-300 mb-3 text-center">
                            ¿Eliminar <span className="font-bold">{agent.name}</span>? Esta acción no se puede deshacer.
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setConfirmDelete(false)}
                                className="flex-1 text-xs py-1.5 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={deleting}
                                className="flex-1 text-xs py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-500 transition-all disabled:opacity-50"
                            >
                                {deleting ? <Loader2 size={12} className="animate-spin mx-auto" /> : 'Confirmar'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

// --------------------------------------------------------------------- //
// AgentsPanel                                                             //
// --------------------------------------------------------------------- //
export const AgentsPanel = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const { agents, loading, error } = useAppSelector(s => s.agents)

    const [showCreateModal, setShowCreateModal] = useState(false)
    const [newAgentName, setNewAgentName] = useState('')
    const [creating, setCreating] = useState(false)
    const [managedAgent, setManagedAgent] = useState<Agent | null>(null)

    useEffect(() => {
        dispatch(fetchAgents())
        dispatch(fetchActiveAgent())
    }, [dispatch])

    const handleActivate = async (agent: Agent) => {
        await dispatch(activateAgent(agent.agent_uuid))
        dispatch(fetchActiveAgent())
    }

    const handleConfigure = async (agent: Agent) => {
        if (!agent.is_active) {
            await dispatch(activateAgent(agent.agent_uuid))
            dispatch(fetchActiveAgent())
        }
        setManagedAgent(null)
        navigate('/config')
    }

    const handleCreate = async () => {
        if (!newAgentName.trim()) return
        setCreating(true)
        await dispatch(createAgent(newAgentName.trim()))
        setCreating(false)
        setNewAgentName('')
        setShowCreateModal(false)
    }

    return (
        <div className="flex flex-col h-full w-full">
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-slate-900/50 backdrop-blur shrink-0">
                <div className="flex items-center gap-2">
                    <Bot size={18} className="text-blue-400" />
                    <h2 className="text-sm font-bold text-slate-100 tracking-wide uppercase">Agentes</h2>
                </div>
                <Button variant="primary" onClick={() => setShowCreateModal(true)} className="flex items-center gap-1.5 text-xs px-3 py-1.5">
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
                        <Button variant="primary" onClick={() => setShowCreateModal(true)} className="text-xs">
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
                            {/* ⚙️ — opens manage modal */}
                            <button
                                onClick={() => setManagedAgent(agent)}
                                title="Gestionar agente"
                                className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-all"
                            >
                                <Settings size={14} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Create Agent Modal */}
            {showCreateModal && (
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
                                onClick={() => { setShowCreateModal(false); setNewAgentName('') }}
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

            {/* Manage Agent Modal */}
            {managedAgent && (
                <ManageModal
                    agent={managedAgent}
                    onClose={() => setManagedAgent(null)}
                    onConfigure={handleConfigure}
                />
            )}
        </div>
    )
}
