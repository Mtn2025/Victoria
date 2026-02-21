/**
 * AgentsPanel.tsx
 * Main view for agent management: list, create, activate, rename, delete.
 *
 * Navigation flow:
 *  - Click on agent card  → activate agent + navigate to /config
 *  - Click on ⚙️ button   → open ManageModal (stopPropagation prevents card nav)
 *  - Modal: pencil ✏️     → inline rename (no navigation)
 *  - Modal: "Configurar"  → activate + navigate to /config
 *  - Modal: delete button → confirmation → delete (disabled for active agent)
 *  - "+ Nuevo Agente"     → open create modal (no navigation)
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
import {
    Bot, Plus, Settings, Loader2, AlertCircle,
    Trash2, Pencil, ArrowRight, X, Check
} from 'lucide-react'
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

    // Name editing
    const [editingName, setEditingName] = useState(false)
    const [name, setName] = useState(agent.name)
    const [saving, setSaving] = useState(false)
    const [nameError, setNameError] = useState('')

    // Delete
    const [confirmDelete, setConfirmDelete] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [deleteError, setDeleteError] = useState('')

    const handleSaveName = async () => {
        if (!name.trim()) { setNameError('El nombre no puede estar vacío'); return }
        if (name.trim() === agent.name) { setEditingName(false); return }
        setSaving(true)
        const result = await dispatch(updateAgentName({ agentUuid: agent.agent_uuid, name: name.trim() }))
        setSaving(false)
        if ((result as any).error) {
            setNameError('Error al guardar el nombre')
        } else {
            setEditingName(false)
            setNameError('')
        }
    }

    const handleDelete = async () => {
        setDeleting(true)
        setDeleteError('')
        const result = await dispatch(deleteAgent(agent.agent_uuid))
        setDeleting(false)
        if ((result as any).error) {
            setDeleteError('No se pudo eliminar. ¿Es el agente activo?')
            setConfirmDelete(false)
        } else {
            onClose()
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={onClose}
        >
            <div
                className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-96 shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
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

                {/* Name row */}
                <label className="block text-xs text-slate-400 mb-1.5">Nombre</label>
                {editingName ? (
                    <div className="flex gap-2 mb-1">
                        <input
                            type="text"
                            value={name}
                            autoFocus
                            onChange={e => { setName(e.target.value); setNameError('') }}
                            onKeyDown={e => {
                                if (e.key === 'Enter') handleSaveName()
                                if (e.key === 'Escape') { setEditingName(false); setName(agent.name) }
                            }}
                            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-blue-500"
                        />
                        <button
                            onClick={handleSaveName}
                            disabled={saving}
                            className="w-8 h-8 mt-1 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center transition-all disabled:opacity-50"
                        >
                            {saving ? <Loader2 size={12} className="animate-spin text-white" /> : <Check size={12} className="text-white" />}
                        </button>
                        <button
                            onClick={() => { setEditingName(false); setName(agent.name) }}
                            className="w-8 h-8 mt-1 rounded-lg bg-slate-700 hover:bg-slate-600 flex items-center justify-center transition-all"
                        >
                            <X size={12} className="text-slate-300" />
                        </button>
                    </div>
                ) : (
                    <div className="flex items-center gap-2 mb-1">
                        <span className="flex-1 text-sm text-slate-100 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700">
                            {name}
                        </span>
                        <button
                            onClick={() => setEditingName(true)}
                            title="Editar nombre"
                            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-all"
                        >
                            <Pencil size={13} />
                        </button>
                    </div>
                )}
                {nameError && <p className="text-xs text-red-400 mb-3">{nameError}</p>}

                {/* Divider */}
                <div className="border-t border-slate-700/60 my-4" />

                {/* Go to Config */}
                <Button
                    variant="primary"
                    onClick={() => onConfigure(agent)}
                    className="w-full flex items-center justify-center gap-2 text-sm mb-3"
                >
                    <ArrowRight size={14} />
                    Configurar agente
                </Button>

                {/* Delete */}
                {deleteError && (
                    <p className="text-xs text-red-400 text-center mb-2">{deleteError}</p>
                )}
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
                            ¿Eliminar <span className="font-bold">{agent.name}</span>? No se puede deshacer.
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

    /** Click on the card: activate + go directly to /config */
    const handleCardClick = async (agent: Agent) => {
        if (!agent.is_active) {
            await dispatch(activateAgent(agent.agent_uuid))
            dispatch(fetchActiveAgent())
        }
        navigate('/config')
    }

    /** ⚙️ button: open manage modal — does NOT navigate */
    const handleManageClick = (e: React.MouseEvent, agent: Agent) => {
        e.stopPropagation()   // prevent card onClick from firing
        setManagedAgent(agent)
    }

    /** "Configurar agente" inside modal: activate + navigate */
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
                <Button
                    variant="primary"
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5"
                >
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
                    /* CARD — clickeable → activa agente y navega a /config */
                    <div
                        key={agent.agent_uuid}
                        onClick={() => handleCardClick(agent)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => e.key === 'Enter' && handleCardClick(agent)}
                        className={cn(
                            "flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer",
                            agent.is_active
                                ? "bg-blue-900/20 border-blue-500/40 ring-1 ring-blue-500/20 hover:ring-blue-500/40"
                                : "bg-slate-800/50 border-slate-700/50 hover:border-slate-500 hover:bg-slate-800"
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
                            {/* ⚙️ — open manage modal (stopPropagation: does NOT trigger card click) */}
                            <button
                                onClick={(e) => handleManageClick(e, agent)}
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
