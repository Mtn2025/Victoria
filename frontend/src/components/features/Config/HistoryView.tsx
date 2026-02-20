import { History } from 'lucide-react'

export const HistoryView = () => {
    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="p-2 bg-slate-500/10 rounded-lg">
                    <History className="w-5 h-5 text-slate-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-white">Historial de Llamadas</h3>
                    <p className="text-xs text-slate-400">Registro detallado de llamadas y sesiones.</p>
                </div>
            </div>

            <div className="p-8 text-center border border-slate-700 rounded-xl bg-slate-800/50">
                <div className="inline-flex p-4 bg-slate-900 rounded-full mb-4">
                    <History className="w-8 h-8 text-slate-500" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Vista de Historial en Desarrollo</h4>
                <p className="text-slate-400 text-sm max-w-md mx-auto">
                    El historial de llamadas se está migrando a un módulo de reportes dedicado con filtros avanzados y exportación.
                </p>
                <button className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-xs font-bold text-white transition-all">
                    Ver Logs Crudos (Legacy)
                </button>
            </div>
        </div>
    )
}
