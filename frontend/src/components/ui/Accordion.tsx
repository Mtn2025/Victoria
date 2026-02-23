import { useState, ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/utils/cn'

interface AccordionProps {
    title: ReactNode
    children: ReactNode
    defaultOpen?: boolean
    isOpen?: boolean
    onToggle?: () => void
    className?: string
    headerClassName?: string
}

export const Accordion = ({
    title,
    children,
    defaultOpen = false,
    isOpen: controlledIsOpen,
    onToggle,
    className,
    headerClassName
}: AccordionProps) => {
    const [internalIsOpen, setInternalIsOpen] = useState(defaultOpen)
    const isControlled = controlledIsOpen !== undefined
    const isOpen = isControlled ? controlledIsOpen : internalIsOpen

    const handleToggle = () => {
        if (onToggle) {
            onToggle()
        }
        if (!isControlled) {
            setInternalIsOpen(!isOpen)
        }
    }

    return (
        <div className={cn("border border-white/10 rounded-xl overflow-hidden bg-slate-900/40", className)}>
            <button
                type="button"
                onClick={handleToggle}
                className={cn(
                    "w-full flex items-center justify-between p-4 bg-slate-800/20 hover:bg-slate-800/50 transition-colors text-sm font-bold tracking-wide uppercase",
                    headerClassName
                )}
            >
                <div className="flex items-center gap-2">
                    {title}
                </div>
                <ChevronDown
                    size={16}
                    className={cn(
                        "text-slate-500 transition-transform duration-200",
                        isOpen ? "rotate-180" : ""
                    )}
                />
            </button>

            <div
                className={cn(
                    "grid transition-all duration-300 ease-in-out",
                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                )}
            >
                <div className="overflow-hidden">
                    <div className="p-4 border-t border-white/5">
                        {children}
                    </div>
                </div>
            </div>
        </div>
    )
}
