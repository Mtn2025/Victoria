import React from 'react'
import { HistoryCall } from '@/types/history'
import { Eye } from 'lucide-react'

interface HistoryTableProps {
    calls: HistoryCall[]
    selectedCalls: string[]
    onSelectCall: (id: string, checked: boolean) => void
    onSelectAll: (checked: boolean) => void
    onViewDetail: (call: HistoryCall) => void
    isLoading: boolean
}

export const HistoryTable: React.FC<HistoryTableProps> = ({
    calls,
    selectedCalls,
    onSelectCall,
    onSelectAll,
    onViewDetail,
    isLoading
}) => {
    const allSelected = calls.length > 0 && selectedCalls.length === calls.length
    const isIndeterminate = selectedCalls.length > 0 && selectedCalls.length < calls.length

    if (isLoading) {
        return <div className="text-center py-8 text-slate-500">Cargando historial...</div>
    }

    if (!calls || calls.length === 0) {
        return <div className="text-center py-8 text-slate-500 italic">No hay historial disponible.</div>
    }

    const getStatusStyle = (status: string | undefined | null) => {
        if (!status) return 'bg-slate-700 text-slate-300'
        switch (status.toLowerCase()) {
            case 'completed': return 'bg-green-900/40 text-green-400 border border-green-700/50'
            case 'voicemail': return 'bg-purple-900/40 text-purple-400 border border-purple-700/50'
            case 'voicemail_delayed': return 'bg-purple-900/20 text-purple-300 border border-purple-800/50'
            case 'busy': return 'bg-orange-900/40 text-orange-400 border border-orange-700/50'
            case 'no_answer': return 'bg-yellow-900/40 text-yellow-400 border border-yellow-700/50'
            case 'failed':
            case 'canceled': return 'bg-red-900/40 text-red-400 border border-red-700/50'
            case 'in_progress':
            case 'ringing':
            case 'dialing': return 'bg-blue-900/40 text-blue-400 border border-blue-700/50 animate-pulse'
            default: return 'bg-slate-700 text-slate-300'
        }
    }

    const getStatusLabel = (status: string | undefined | null) => {
        if (!status) return 'N/A'
        switch (status.toLowerCase()) {
            case 'completed': return 'Completada'
            case 'voicemail': return 'Buzón Directo'
            case 'voicemail_delayed': return 'Buzón (Timbres)'
            case 'busy': return 'Rechazado'
            case 'no_answer': return 'Sin Respuesta'
            case 'failed': return 'Fallida'
            case 'canceled': return 'Cancelada'
            case 'in_progress': return 'En curso'
            case 'ringing': return 'Timbrando'
            case 'dialing': return 'Marcando'
            default: return status
        }
    }

    return (
        <div className="overflow-x-auto rounded border border-slate-700 h-full">
            <table className="w-full text-xs text-left text-slate-400">
                <thead className="text-xs text-slate-300 uppercase bg-slate-800 sticky top-0 z-10">
                    <tr>
                        <th scope="col" className="px-4 py-2 w-8">
                            <input
                                type="checkbox"
                                checked={allSelected}
                                ref={el => el && (el.indeterminate = isIndeterminate)}
                                onChange={(e) => onSelectAll(e.target.checked)}
                                className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-600 ring-offset-slate-800 focus:ring-2"
                            />
                        </th>
                        <th scope="col" className="px-4 py-2">Fecha</th>
                        <th scope="col" className="px-4 py-2">Fuente</th>
                        <th scope="col" className="px-4 py-2">Duración</th>
                        <th scope="col" className="px-4 py-2">Status</th>
                        <th scope="col" className="px-4 py-2">Acción</th>
                    </tr>
                </thead>
                <tbody className="overflow-y-auto">
                    {calls.map((call) => (
                        <tr key={call.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                            <td className="px-4 py-2">
                                <input
                                    type="checkbox"
                                    checked={selectedCalls.includes(call.id)}
                                    onChange={(e) => onSelectCall(call.id, e.target.checked)}
                                    className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-600 ring-offset-slate-800 focus:ring-2"
                                />
                            </td>
                            <td className="px-4 py-2 font-mono whitespace-nowrap">
                                {new Date(call.start_time).toLocaleString()}
                            </td>
                            <td className="px-4 py-2">
                                {call.client_type === 'telnyx' && (
                                    <span className="px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-400 border border-emerald-700/50">Telnyx</span>
                                )}
                                {call.client_type === 'twilio' && (
                                    <span className="px-2 py-0.5 rounded bg-red-900/40 text-red-400 border border-red-700/50">Twilio</span>
                                )}
                                {call.client_type === 'browser' && (
                                    <span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-400 border border-blue-700/50">Simulador</span>
                                )}
                                {(!call.client_type || call.client_type === 'unknown') && (
                                    <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/50">Desconocido</span>
                                )}
                            </td>
                            <td className="px-4 py-2 font-mono">
                                {call.duration_seconds !== null && call.duration_seconds !== undefined ? `${parseFloat(call.duration_seconds.toString()).toFixed(2)}s` : <span className="text-yellow-500 animate-pulse">En curso</span>}
                            </td>
                            <td className="px-4 py-2">
                                <span className={`uppercase text-[10px] font-bold px-2 py-0.5 rounded ${getStatusStyle(call.status)}`}>
                                    {getStatusLabel(call.status)}
                                </span>
                            </td>
                            <td className="px-4 py-2">
                                <button
                                    type="button"
                                    onClick={() => onViewDetail(call)}
                                    className="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1 transition-colors"
                                >
                                    <Eye size={14} /> Ver
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
