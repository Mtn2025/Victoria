import React from 'react'
import { Modal } from '@/components/ui/Modal'
import { HistoryCall, TranscriptLine } from '@/types/history'
import { Clock, Calendar, Phone, Activity, User, Bot, FileText } from 'lucide-react'

interface CallDetailModalProps {
    call: HistoryCall | null
    isOpen: boolean
    onClose: () => void
    transcript?: TranscriptLine[]
}

export const CallDetailModal: React.FC<CallDetailModalProps> = ({ call, isOpen, onClose, transcript }) => {
    if (!call) return null

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Detalle de Llamada" size="xl">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
                {/* Left: Metadata */}
                <div className="lg:col-span-1 space-y-6 overflow-y-auto pr-2">
                    {/* Status Card */}
                    <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400 text-xs uppercase tracking-wider">Estado</span>
                            <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${call.status === 'completed' ? 'bg-green-900/40 text-green-400' :
                                'bg-slate-700 text-slate-300'
                                }`}>
                                {call.status || 'Desconocido'}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 text-2xl font-mono text-white">
                            <Clock size={20} className="text-blue-400" />
                            {call.duration_seconds ? `${call.duration_seconds}s` : '--'}
                        </div>
                    </div>

                    {/* Info List */}
                    <div className="bg-slate-800/30 rounded-xl border border-slate-700 divide-y divide-slate-700/50">
                        <div className="p-3 flex items-center gap-3">
                            <Calendar size={16} className="text-slate-500" />
                            <div>
                                <div className="text-[10px] text-slate-500 uppercase">Fecha</div>
                                <div className="text-sm text-slate-200">{new Date(call.start_time).toLocaleString()}</div>
                            </div>
                        </div>
                        <div className="p-3 flex items-center gap-3">
                            <Activity size={16} className="text-slate-500" />
                            <div>
                                <div className="text-[10px] text-slate-500 uppercase">Proveedor</div>
                                <div className="text-sm text-slate-200 capitalize">{call.client_type}</div>
                            </div>
                        </div>
                        <div className="p-3 flex items-center gap-3">
                            <Phone size={16} className="text-slate-500" />
                            <div>
                                <div className="text-[10px] text-slate-500 uppercase">ID de Llamada</div>
                                <div className="text-xs font-mono text-slate-400 break-all">{call.id}</div>
                            </div>
                        </div>
                    </div>

                    {/* Extracted Data (if any) */}
                    {call.extracted_data && Object.keys(call.extracted_data).length > 0 && (
                        <div className="bg-slate-800/30 rounded-xl border border-slate-700 p-4">
                            <h4 className="text-xs text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <FileText size={14} /> Datos Extraídos
                            </h4>
                            <div className="space-y-2">
                                {Object.entries(call.extracted_data).map(([key, value]) => (
                                    <div key={key} className="flex justify-between text-sm group">
                                        <span className="text-slate-500 group-hover:text-slate-400 transition-colors">{key}:</span>
                                        <span className="text-slate-200 font-medium">{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Transcript */}
                <div className="lg:col-span-2 bg-slate-950 rounded-xl border border-slate-800 flex flex-col overflow-hidden">
                    <div className="p-3 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                        <h4 className="text-sm font-medium text-slate-300">Transcripción</h4>
                        {/* Audio Player Placeholder */}
                        <div className="text-xs text-slate-500 flex items-center gap-2">
                            <span>Audio no disponible</span>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                        {transcript && transcript.length > 0 ? (
                            transcript.map((line, idx) => (
                                <div key={idx} className={`flex gap-3 ${line.role === 'assistant' ? 'flex-row' : 'flex-row-reverse'}`}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${line.role === 'assistant' ? 'bg-blue-600/20 text-blue-400' : 'bg-emerald-600/20 text-emerald-400'
                                        }`}>
                                        {line.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                                    </div>
                                    <div className={`flex flex-col max-w-[80%] ${line.role === 'assistant' ? 'items-start' : 'items-end'}`}>
                                        <div className={`px-4 py-2 rounded-2xl text-sm ${line.role === 'assistant'
                                            ? 'bg-slate-800 text-slate-200 rounded-tl-none'
                                            : 'bg-emerald-900/20 text-emerald-100 rounded-tr-none border border-emerald-900/30'
                                            }`}>
                                            {line.content}
                                        </div>
                                        <span className="text-[10px] text-slate-600 mt-1">
                                            {line.timestamp || '00:00'}
                                        </span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-2">
                                <FileText size={32} className="opacity-20" />
                                <p>No hay transcripción disponible</p>
                            </div>
                        )}
                        <div className="text-right font-mono text-white">
                            {new Date(call.start_time).toLocaleString()}
                        </div>
                        <div className="text-slate-400">Duración</div>
                        <div className="text-right font-mono text-white">
                            {call.duration_seconds || 0}s
                        </div>
                        {/* Cost - Not in type yet
                        <div className="text-slate-400">Costo</div>
                        <div className="text-right font-mono text-white">
                            ${call.cost?.toFixed(4) || '0.000'}
                        </div>
                        */}
                    </div>
                </div>
            </div>
        </Modal>
    )
}
