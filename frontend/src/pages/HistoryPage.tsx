import { useEffect, useState } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { HistoryFilters } from '@/components/features/History/HistoryFilters'
import { HistoryTable } from '@/components/features/History/HistoryTable'
import { CallDetailModal } from '@/components/features/History/CallDetailModal'
import { historyService } from '@/services/historyService'
import { HistoryCall, CallDetail } from '@/types/history'
import { Button } from '@/components/ui/Button'
import { Trash2, RefreshCw, Download } from 'lucide-react'

export const HistoryPage = () => {
    const [calls, setCalls] = useState<HistoryCall[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [activeFilter, setActiveFilter] = useState('all')
    const [selectedCalls, setSelectedCalls] = useState<string[]>([])
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [selectedCall, setSelectedCall] = useState<CallDetail | null>(null) // Use CallDetail type
    const [isDetailOpen, setIsDetailOpen] = useState(false)

    // Load Data
    const loadHistory = async () => {
        setIsLoading(true)
        try {
            const response = await historyService.getHistory(page, 20, activeFilter)

            setCalls(response.calls)
            setTotalPages(Math.ceil(response.total / 20))
        } catch (error) {
            console.error('Error loading history:', error)
            setCalls([])
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        loadHistory()
    }, [page, activeFilter])

    // Handlers
    const handleSelectCall = (id: string, checked: boolean) => {
        if (checked) {
            setSelectedCalls(prev => [...prev, id])
        } else {
            setSelectedCalls(prev => prev.filter(c => c !== id))
        }
    }

    const handleSelectAll = (checked: boolean) => {
        if (checked) {
            setSelectedCalls(calls.map(c => c.id))
        } else {
            setSelectedCalls([])
        }
    }

    const handleDeleteSelected = async () => {
        if (!confirm(`¿Borrar ${selectedCalls.length} llamadas?`)) return

        try {
            await historyService.deleteCalls(selectedCalls)
            setSelectedCalls([])
            loadHistory()
        } catch (error) {
            alert('Error al borrar llamadas')
        }
    }

    const handleExport = () => {
        if (calls.length === 0) return

        const headers = ['ID', 'Fecha', 'Tipo', 'Duración (s)', 'Status']
        const csvContent = [
            headers.join(','),
            ...calls.map(c => [
                c.id,
                new Date(c.start_time).toISOString(),
                c.client_type,
                c.duration_seconds || 0,
                c.status || 'unknown'
            ].join(','))
        ].join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `victoria_history_${new Date().toISOString().slice(0, 10)}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }

    const ViewDetail = async (call: HistoryCall) => {
        try {
            const detail = await historyService.getCallDetail(call.id)
            setSelectedCall(detail)
            setIsDetailOpen(true)
        } catch (error) {
            console.error("Error fetching detail", error)
        }
    }

    // Adapter for legacy modal if needed, or update modal to accept CallDetail
    // For now assuming CallDetailModal handles the detail object or we adapt.
    // Actually CallDetailModal likely expects 'Call'. We might need to refactor it too.
    // Let's pass the 'call' object for list props, and fetch full detail inside.

    return (
        <DashboardLayout>
            <div className="space-y-4 animate-fade-in-up p-6 h-full flex flex-col">
                {/* Header Info */}
                <div className="flex items-center space-x-2 mb-4 shrink-0">
                    <div className="p-2 bg-slate-500/10 rounded-lg">
                        <RefreshCw className="w-6 h-6 text-slate-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">Registro de Llamadas</h3>
                        <p className="text-xs text-slate-400">Detalle completo de sesiones y actividad.</p>
                    </div>
                </div>

                {/* Toolbar */}
                <div className="flex justify-between items-center shrink-0">
                    <HistoryFilters
                        activeFilter={activeFilter}
                        onFilterChange={(f) => { setActiveFilter(f); setPage(1); }}
                    />

                    <div className="flex gap-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={handleExport}
                            className="flex items-center gap-2"
                        >
                            <Download size={14} />
                            Exportar CSV
                        </Button>

                        {selectedCalls.length > 0 && (
                            <Button
                                variant="danger"
                                size="sm"
                                onClick={handleDeleteSelected}
                                className="flex items-center gap-2"
                            >
                                <Trash2 size={14} />
                                Borrar ({selectedCalls.length})
                            </Button>
                        )}
                    </div>
                </div>

                {/* Table */}
                <div className="flex-1 min-h-0 overflow-hidden">
                    <HistoryTable
                        calls={calls}
                        selectedCalls={selectedCalls}
                        onSelectCall={handleSelectCall}
                        onSelectAll={handleSelectAll}
                        onViewDetail={ViewDetail}
                        isLoading={isLoading}
                    />
                </div>

                {/* Pagination */}
                <div className="flex justify-between items-center bg-slate-900/30 p-2 rounded-lg border border-slate-700/50 shrink-0">
                    <div className="text-xs text-slate-500">
                        Página {page} de {totalPages || 1}
                    </div>
                    <div className="flex space-x-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={page <= 1}
                            onClick={() => setPage(p => p - 1)}
                        >
                            &larr; Anterior
                        </Button>
                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={page >= totalPages}
                            onClick={() => setPage(p => p + 1)}
                        >
                            Siguiente &rarr;
                        </Button>
                    </div>
                </div>
            </div>

            {/* Note: We might need to update CallDetailModal types if strict */}
            {selectedCall && (
                <CallDetailModal
                    call={selectedCall.call}
                    isOpen={isDetailOpen}
                    onClose={() => setIsDetailOpen(false)}
                    transcript={selectedCall.transcripts}
                />
            )}
        </DashboardLayout>
    )
}
