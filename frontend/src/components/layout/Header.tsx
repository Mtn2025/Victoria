import { SignalHigh } from "lucide-react"

export const Header = () => {
    return (
        <div className="h-16 flex items-center justify-between px-8 border-b border-white/5 shrink-0 bg-slate-950/50 backdrop-blur-sm">
            <h1 className="font-bold text-lg text-slate-100">Simulador de Conversación</h1>
            <div className="flex items-center space-x-4 text-xs text-slate-500">
                <span className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Sistema en línea
                </span>
                <div className="h-4 w-px bg-white/10" />
                <span className="flex items-center gap-2 text-slate-400">
                    <SignalHigh size={14} />
                    5ms
                </span>
            </div>
        </div>
    )
}
