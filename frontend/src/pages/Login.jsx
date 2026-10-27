import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { authService } from '../services/authService'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  const from = location.state?.from?.pathname || '/dashboard'

  // Redirect if already authenticated
  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate('/dashboard', { replace: true })
      return
    }
    // Pre-fill email if passed from signup
    if (location.state?.registeredEmail || location.state?.email) {
      setEmail(location.state.registeredEmail || location.state.email)
    }
    if (location.state?.successMessage) {
      setSuccessMsg(location.state.successMessage)
    }
  }, [navigate, location])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setLoading(true)

    try {
      await authService.login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Invalid email or password. Please check your credentials.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleAutofillDemo = (roleEmail, rolePass) => {
    setEmail(roleEmail)
    setPassword(rolePass)
    setError(null)
    setSuccessMsg(null)
  }

  return (
    <div className="w-full flex flex-col justify-center items-center my-auto relative">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Login Card - max-width 580px with generous, balanced padding (40px) */}
      <div className="w-full max-w-[580px] bg-slate-900/90 border border-slate-800/90 rounded-3xl p-8 sm:p-10 shadow-2xl shadow-black/80 backdrop-blur-xl relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-7">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white font-black text-2xl shadow-lg shadow-indigo-500/30 mx-auto mb-5">
            ₹
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">FinRecon Control Center</h2>
          <p className="text-sm text-slate-400 mt-2.5 font-normal">
            Enterprise Payment Reconciliation & AI Agent Operations
          </p>
        </div>

        {/* Success notification (e.g. redirected from Signup) */}
        {successMsg && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs sm:text-sm flex items-center gap-2.5">
            <span className="text-base">✅</span>
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error notification */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs sm:text-sm flex items-center gap-2.5">
            <span className="text-base">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin}>
          {/* Email field: 6px to 8px label spacing */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@acme.com"
              className="w-full h-11 px-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
            />
          </div>

          {/* Password field: 20px to 24px above */}
          <div className="mt-5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-11 px-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
            />
          </div>

          {/* Login Button: 22px to 26px spacing above */}
          <div className="mt-6">
            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading ? 'Authenticating...' : 'Sign In to Control Center'}
            </button>
          </div>
        </form>

        {/* Demo Credentials Quick-Fill: 24px spacing above, 12px below heading */}
        <div className="mt-7 pt-6 border-t border-slate-800/80">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 text-center mb-3">
            Quick-Fill Demo Credentials
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleAutofillDemo('admin@fintech.test', 'Admin1234!')}
              className="p-3.5 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-left transition-all cursor-pointer group"
            >
              <span className="block text-xs font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">Finance Admin</span>
              <span className="text-[11px] text-slate-400 mt-0.5 block">Full platform rights</span>
            </button>
            <button
              type="button"
              onClick={() => handleAutofillDemo('operator@fintech.test', 'Operator1234!')}
              className="p-3.5 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-left transition-all cursor-pointer group"
            >
              <span className="block text-xs font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">Ops Operator</span>
              <span className="text-[11px] text-slate-400 mt-0.5 block">Triage & review</span>
            </button>
          </div>
        </div>

        {/* Sign Up Option: Immediately below demo credentials with 20px spacing */}
        <div className="mt-5 text-center">
          <p className="text-sm text-slate-400">
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors ml-1 underline-offset-4 hover:underline"
            >
              Sign Up
            </Link>
          </p>
        </div>
      </div>

      {/* Footer Info with comfortable spacing: 24px above */}
      <div className="mt-6 text-center text-xs text-slate-500 tracking-wide z-10 px-4">
        Deterministic Multi-Rail Match Engine · Immutable Ledger Guardrails
      </div>
    </div>
  )
}
