import { useState, useEffect, useCallback } from 'react'
import { Outlet } from 'react-router-dom'
import { DashboardLayout } from './DashboardLayout'
// ConfigPage is in src/pages, MainLayout is in src/components/layout
import { ConfigPage } from '../../pages/ConfigPage'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { setSidebarWidth } from '@/store/slices/uiSlice'

export const MainLayout = () => {
    const dispatch = useAppDispatch()
    const sidebarWidth = useAppSelector(state => state.ui.sidebarWidth)

    // activeTab logic removed, router handles views

    const [isResizing, setIsResizing] = useState(false)

    const startResizing = useCallback(() => {
        setIsResizing(true)
    }, [])

    const stopResizing = useCallback(() => {
        setIsResizing(false)
    }, [])

    const resize = useCallback(
        (mouseMoveEvent: MouseEvent) => {
            if (isResizing) {
                // 64 is Sidebar width
                let newWidth = mouseMoveEvent.clientX - 64
                if (newWidth < 320) newWidth = 320
                if (newWidth > 800) newWidth = 800

                dispatch(setSidebarWidth(newWidth))
            }
        },
        [isResizing, dispatch]
    )

    useEffect(() => {
        window.addEventListener("mousemove", resize)
        window.addEventListener("mouseup", stopResizing)
        return () => {
            window.removeEventListener("mousemove", resize)
            window.removeEventListener("mouseup", stopResizing)
        }
    }, [resize, stopResizing])

    return (
        <DashboardLayout>
            {/* Config Panel (Resizable) */}
            <aside
                className="flex-none flex flex-col bg-slate-900/90 backdrop-blur-md border-r border-white/5 z-20 relative shadow-2xl shrink-0"
                style={{ width: sidebarWidth }}
            >
                {/* Resize Handle */}
                <div
                    className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500/50 z-[100] transition-colors"
                    onMouseDown={startResizing}
                />

                <ConfigPage />
            </aside>

            {/* Main Content via Router */}
            <div className="flex-1 overflow-hidden bg-slate-950 relative">
                <Outlet />
            </div>
        </DashboardLayout>
    )
}

