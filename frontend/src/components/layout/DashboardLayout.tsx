import React from 'react'
import { Sidebar } from './Sidebar'

interface DashboardLayoutProps {
    children: React.ReactNode
}

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
    return (
        <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-200">
            <Sidebar />
            <div className="flex flex-1 overflow-hidden relative">
                {children}
            </div>
        </div>
    )
}
