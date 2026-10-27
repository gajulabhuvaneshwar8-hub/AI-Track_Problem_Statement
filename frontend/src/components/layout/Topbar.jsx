import React from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { authService } from '../../services/authService'
import HealthBadge from '../HealthBadge'

const ROUTE_NAMES = {
  '/': 'Control Center',
  '/dashboard': 'Control Center',
  '/transactions': 'Transactions Ledger',
  '/reconciliation': 'Reconciliation Engine',
  '/exceptions': 'Exception Management',
  '/agent': 'AI Agent Investigation',
  '/ai-analysis': 'AI Mismatch Diagnostics',
  '/import': 'Data Ingestion Hub',
  '/settlements': 'Settlements Ledger',
  '/merchants': 'Merchants Directory',
}

export default function Topbar({ onToggleSidebar }) {
  const location = useLocation()
  const navigate = useNavigate()
  const user = authService.getCurrentUser()

  const handleLogout = () => {
    authService.logout()
    navigate('/login')
  }

  const currentTitle = ROUTE_NAMES[location.pathname] || 'Control Center'

  return (
    <header className="sticky top-0 z-30 h-16 w-full bg-slate-900/80 border-b border-slate-800 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg lg:hidden"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Breadcrumb path */}
        <div className="flex items-center gap-2 text-xs">
          <Link to="/dashboard" className="text-slate-400 hover:text-slate-200 transition-colors">
            FinOps
          </Link>
          <span className="text-slate-600">/</span>
          <span className="text-slate-200 font-semibold">{currentTitle}</span>
        </div>
      </div>

      {/* Right: Health Badge, Profile, Logout */}
      <div className="flex items-center gap-3 sm:gap-4">
        <HealthBadge />

        <div className="hidden sm:block h-5 w-px bg-slate-800" />

        <div className="flex items-center gap-2.5">
          <div className="hidden md:flex flex-col text-right">
            <span className="text-xs font-semibold text-slate-200">{user?.name || user?.email}</span>
            <span className="text-[10px] text-slate-400 capitalize">
              {user?.role ? String(user.role).replace(/_/g, ' ') : 'Finance User'}
            </span>
          </div>

          <button
            onClick={handleLogout}
            title="Sign Out"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400 text-slate-400 text-xs font-medium transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>
  )
}
