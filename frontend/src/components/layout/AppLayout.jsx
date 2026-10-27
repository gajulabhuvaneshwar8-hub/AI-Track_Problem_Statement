import React from 'react'
import { Outlet } from 'react-router-dom'
import TopNavbar from './TopNavbar'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 w-[600px] h-[600px] bg-indigo-600/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 right-10 w-[500px] h-[500px] bg-cyan-600/5 rounded-full blur-3xl" />
      </div>

      {/* Full-width Top Horizontal Navigation Bar */}
      <TopNavbar />

      {/* Main Content Area - Full width with no left sidebar margins/paddings */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto z-10">
        <Outlet />
      </main>
    </div>
  )
}
