import { useState, useEffect, useCallback } from 'react'
import { Outlet } from 'react-router-dom'
import { DashboardLayout } from './DashboardLayout'

/**
 * MainLayout
 *
 * Thin layout shell — all page content goes through <Outlet />.
 * ConfigPage was previously hardcoded here AND rendered via Outlet,
 * causing it to appear twice. Now ALL content is router-driven.
 */
export const MainLayout = () => {
    return (
        <DashboardLayout>
            <div className="flex-1 overflow-hidden bg-slate-950 relative">
                <Outlet />
            </div>
        </DashboardLayout>
    )
}
