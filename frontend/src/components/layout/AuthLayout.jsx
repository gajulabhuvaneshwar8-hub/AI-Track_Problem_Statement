import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { authService } from '../../services/authService'
import TopNavbar from './TopNavbar'

/**
 * AuthLayout
 * 
 * Layout shell for authentication pages (/login, /signup).
 * - Displays the top horizontal navbar at the top of the viewport.
 * - Centers the authentication card in the remaining viewport area without left sidebar offsets.
 * - Redirects authenticated users to /dashboard.
 */
export default function AuthLayout() {
  const isAuth = authService.isAuthenticated()

  // Redirect authenticated users away from public auth pages
  if (isAuth) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen w-full bg-slate-950 flex flex-col font-sans relative selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 w-[600px] h-[600px] bg-indigo-600/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 right-10 w-[500px] h-[500px] bg-cyan-600/5 rounded-full blur-3xl" />
      </div>

      {/* Top Navbar */}
      <TopNavbar />

      {/* Centered Auth Card Container */}
      <main className="flex-1 flex flex-col justify-center items-center p-4 sm:p-6 w-full z-10">
        <Outlet />
      </main>
    </div>
  )
}
