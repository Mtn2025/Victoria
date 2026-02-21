import { FEATURES, FeatureKey } from '@/utils/featureFlags'

interface FeatureGateProps {
    feature: FeatureKey
    children: React.ReactNode
    /** Qué mostrar cuando la feature está desactivada. Default: <ComingSoon /> */
    fallback?: React.ReactNode
}

/**
 * FeatureGate — Envuelve components con un flag de activación.
 *
 * Uso:
 *   <FeatureGate feature="SIMULATOR_PANEL">
 *     <SimulatorPage />
 *   </FeatureGate>
 *
 * Si FEATURES.SIMULATOR_PANEL === false, muestra el fallback en lugar del componente.
 * Si FEATURES.SIMULATOR_PANEL === true, monta el componente normalmente.
 */
export const FeatureGate = ({ feature, children, fallback }: FeatureGateProps) => {
    if (!FEATURES[feature]) {
        return fallback !== undefined ? <>{fallback}</> : <ComingSoon name={feature} />
    }
    return <>{children}</>
}

/** Placeholder visual para features desactivados */
export const ComingSoon = ({ name }: { name?: string }) => (
    <div className="flex flex-col items-center justify-center h-full w-full bg-slate-950 text-slate-600 select-none gap-3">
        <div className="text-5xl">⬛</div>
        <p className="text-sm font-mono">
            {name ? `[${name}]` : 'SECCIÓN'} — en construcción
        </p>
    </div>
)
