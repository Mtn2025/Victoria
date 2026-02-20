import { cn } from "@/utils/cn"
import { Loader2 } from "lucide-react"

interface LoadingSpinnerProps {
    className?: string
    size?: number
}

export const LoadingSpinner = ({ className, size = 24 }: LoadingSpinnerProps) => {
    return (
        <Loader2
            className={cn("animate-spin text-blue-500", className)}
            size={size}
        />
    )
}
