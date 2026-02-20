import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from "@/utils/cn"
import { Loader2 } from "lucide-react"

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' | 'glass'
    size?: 'sm' | 'md' | 'lg' | 'icon'
    isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {

        const variants = {
            primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20",
            secondary: "bg-slate-700 hover:bg-slate-600 text-white",
            ghost: "hover:bg-slate-800/50 text-slate-400 hover:text-white",
            danger: "bg-red-600 hover:bg-red-500 text-white",
            outline: "border border-slate-700 hover:bg-slate-800 text-slate-300",
            glass: "bg-white/5 hover:bg-white/10 text-white border border-white/10 backdrop-blur-sm"
        }

        const sizes = {
            sm: "h-8 px-3 text-xs",
            md: "h-10 px-4 py-2",
            lg: "h-12 px-6 text-lg",
            icon: "h-10 w-10 p-0 flex items-center justify-center rounded-xl"
        }

        return (
            <button
                ref={ref}
                className={cn(
                    "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus:ring-2 focus:ring-blue-500/50",
                    variants[variant],
                    sizes[size],
                    className
                )}
                disabled={isLoading || props.disabled}
                {...props}
            >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {children}
            </button>
        )
    }
)

Button.displayName = "Button"

export { Button }
