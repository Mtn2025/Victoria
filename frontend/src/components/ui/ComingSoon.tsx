/**
 * ComingSoon.tsx
 * Placeholder stub para tabs/secciones que aún no están
 * conectadas correctamente al backend.
 * Se usa durante la reconstrucción metodológica del dashboard.
 * NO ELIMINAR — reemplazar gradualmente por los componentes reales.
 */

interface ComingSoonProps {
    tabName: string
    /** Descripción opcional de qué necesita implementarse */
    reason?: string
}

export const ComingSoon = ({ tabName, reason }: ComingSoonProps) => {
    return (
        <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center px-6 py-12 select-none">
            {/* Icon */}
            <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center mb-5 shadow-inner">
                <span className="text-3xl">🔧</span>
            </div>

            {/* Title */}
            <h3 className="text-base font-semibold text-slate-200 mb-1">
                {tabName}
            </h3>

            {/* Badge */}
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-4">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                En reconstrucción
            </span>

            {/* Description */}
            <p className="text-sm text-slate-500 max-w-xs leading-relaxed">
                {reason
                    ? reason
                    : 'Esta sección está siendo reconstruida para conectarse correctamente al backend. Pronto estará disponible.'}
            </p>
        </div>
    )
}
