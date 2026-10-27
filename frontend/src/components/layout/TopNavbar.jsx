import React from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'
import { authService } from '../../services/authService'
import HealthBadge from '../HealthBadge'

export const NAV_ITEMS = [
  {
    label: 'Control Center',
    path: '/dashboard',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    label: 'Transactions',
    path: '/transactions',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
  },
  {
    label: 'Reconciliation',
    path: '/reconciliation',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    label: 'Exceptions',
    path: '/exceptions',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    label: 'AI Agent Triage',
    path: '/agent',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    label: 'AI Analysis',
    path: '/ai-analysis',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    label: 'Data Ingestion',
    path: '/import',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
  {
    label: 'Settlements',
    path: '/settlements',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    label: 'Merchants',
    path: '/merchants',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
]

export default function TopNavbar() {
  const navigate = useNavigate()
  const isAuth = authService.isAuthenticated()
  const user = isAuth ? authService.getCurrentUser() : null

  const handleLogout = () => {
    authService.logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-900/95 border-b border-slate-800 backdrop-blur-md shadow-lg shadow-black/30">
      <div className="max-w-[1700px] mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-[72px] sm:h-[74px] gap-3">
          {/* Brand: Finance Operations */}
          <Link
            to={isAuth ? '/dashboard' : '/login'}
            className="flex items-center gap-3 flex-shrink-0 group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white font-black text-lg shadow-md shadow-indigo-500/25 group-hover:scale-105 transition-transform">
              ₹
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[19px] font-semibold text-white tracking-tight leading-tight">
                Finance Operations
              </span>
              <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-widest bg-indigo-500/15 px-2 py-0.5 rounded-md border border-indigo-500/25">
                AI
              </span>
            </div>
          </Link>

          {/* Horizontal Navigation Items */}
          <nav className="flex-1 flex items-center gap-2 overflow-x-auto no-scrollbar py-1 px-2 mx-1 sm:mx-3">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm sm:text-[15px] lg:text-[16px] leading-[1.4] whitespace-nowrap transition-all flex-shrink-0 cursor-pointer ${
                    isActive
                      ? 'bg-indigo-600/25 text-indigo-200 border border-indigo-500/40 shadow-sm shadow-indigo-500/15 font-semibold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent font-medium'
                  }`
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Right Action Area */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <HealthBadge />

            {isAuth ? (
              <>
                <div className="hidden sm:block h-6 w-px bg-slate-800" />

                {/* User Profile */}
                <div className="hidden lg:flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center font-bold text-sm uppercase">
                    {user?.name?.[0] || user?.email?.[0] || 'U'}
                  </div>
                  <div className="flex flex-col text-right">
                    <span className="text-sm font-semibold text-slate-200 max-w-[130px] truncate leading-tight">
                      {user?.name || user?.email}
                    </span>
                    <span className="text-xs text-slate-400 capitalize leading-tight">
                      {user?.role ? String(user.role).replace(/_/g, ' ') : 'Finance User'}
                    </span>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-800 bg-slate-900 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400 text-slate-300 text-sm font-medium transition-all cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span className="hidden md:inline">Logout</span>
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2.5">
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="px-3.5 py-1.5 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-600/30"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
