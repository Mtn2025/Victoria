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
                                {(!call.client_type || call.client_type === 'browser') && (
                                    <span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-400 border border-blue-700/50">Simulador</span>
                                )}
                            </td>
                            <td className="px-4 py-2 font-mono">
                                {call.duration_seconds ? `${call.duration_seconds}s` : <span className="text-yellow-500 animate-pulse">En curso</span>}
                            </td>
                            <td className="px-4 py-2">
                                <span className="uppercase text-[10px] font-bold opacity-70">{call.status || 'N/A'}</span>
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
