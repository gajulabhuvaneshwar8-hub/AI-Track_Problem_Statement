import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService, registerUser } from '../services/authService'

export default function Signup() {
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })

  const [touched, setTouched] = useState({})
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Redirect to dashboard if user is already authenticated
  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate('/dashboard', { replace: true })
    }
  }, [navigate])

  const validateField = (field, value, allValues = formData) => {
    switch (field) {
      case 'name':
        if (!value.trim()) return 'Full name is required'
        if (value.trim().length < 2) return 'Full name must be at least 2 characters'
        return null

      case 'email':
        if (!value.trim()) return 'Email address is required'
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(value.trim())) return 'Please enter a valid email address'
        return null

      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        return null

      case 'confirmPassword':
        if (!value) return 'Please confirm your password'
        if (value !== allValues.password) return 'Passwords do not match'
        return null

      default:
        return null
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    const updated = { ...formData, [name]: value }
    setFormData(updated)

    if (touched[name]) {
      const err = validateField(name, value, updated)
      setFieldErrors((prev) => ({ ...prev, [name]: err }))
    }

    // Also revalidate confirmPassword if password changes
    if (name === 'password' && touched.confirmPassword) {
      const confirmErr = validateField('confirmPassword', updated.confirmPassword, updated)
      setFieldErrors((prev) => ({ ...prev, confirmPassword: confirmErr }))
    }
  }

  const handleBlur = (e) => {
    const { name, value } = e.target
    setTouched((prev) => ({ ...prev, [name]: true }))
    const err = validateField(name, value, formData)
    setFieldErrors((prev) => ({ ...prev, [name]: err }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setServerError(null)

    // Mark all fields as touched
    const allTouched = { name: true, email: true, password: true, confirmPassword: true }
    setTouched(allTouched)

    // Validate all fields
    const errors = {
      name: validateField('name', formData.name, formData),
      email: validateField('email', formData.email, formData),
      password: validateField('password', formData.password, formData),
      confirmPassword: validateField('confirmPassword', formData.confirmPassword, formData),
    }
    setFieldErrors(errors)

    if (Object.values(errors).some(Boolean)) {
      return
    }

    setLoading(true)

    try {
      // Send only required fields; role defaults to finance_user on backend
      await registerUser({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      })

      setSuccessMessage('Account created successfully. Redirecting to login...')

      // Redirect to login after brief delay to show success state
      setTimeout(() => {
        navigate('/login', {
          state: {
            registeredEmail: formData.email.trim().toLowerCase(),
            successMessage: 'Account created successfully. Please sign in.',
          },
          replace: true,
        })
      }, 1400)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 409 || (status === 400 && typeof detail === 'string' && (detail.toLowerCase().includes('already registered') || detail.toLowerCase().includes('already exists')))) {
        setServerError('An account with this email already exists.')
      } else if (status === 400) {
        setServerError(typeof detail === 'string' ? detail : 'Registration failed. Please verify your details.')
      } else if (status === 422) {
        setServerError('Please check the information entered.')
      } else {
        setServerError('A server error occurred. Please try again later.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full flex flex-col justify-center items-center my-auto relative">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Signup Card */}
      <div className="w-full max-w-[580px] bg-slate-900/90 border border-slate-800/90 rounded-3xl p-8 sm:p-10 shadow-2xl shadow-black/80 backdrop-blur-xl relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white font-black text-2xl shadow-lg shadow-indigo-500/30 mx-auto mb-5">
            ₹
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Create your FinRecon Account</h2>
          <p className="text-sm text-slate-400 mt-2.5 font-normal">
            Set up your finance operations account to get started.
          </p>
        </div>

        {/* Server error notification */}
        {serverError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs sm:text-sm flex items-center gap-2.5 animate-fadeIn">
            <span className="text-base">⚠️</span>
            <span>{serverError}</span>
          </div>
        )}

        {/* Success notification */}
        {successMessage && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs sm:text-sm flex items-center gap-2.5 animate-fadeIn">
            <span className="text-base">✅</span>
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-[18px]">
          {/* Full Name */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Full Name
            </label>
            <input
              type="text"
              name="name"
              required
              disabled={loading || Boolean(successMessage)}
              value={formData.name}
              onChange={handleChange}
              onBlur={handleBlur}
              placeholder="Jane Doe"
              className={`w-full h-11 px-4 rounded-xl bg-slate-950 border ${
                fieldErrors.name && touched.name ? 'border-rose-500/80 focus:border-rose-500' : 'border-slate-800 focus:border-indigo-500'
              } text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all`}
            />
            {fieldErrors.name && touched.name && (
              <p className="text-xs text-rose-400 mt-1.5 font-medium">{fieldErrors.name}</p>
            )}
          </div>

          {/* Email Address */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              required
              disabled={loading || Boolean(successMessage)}
              value={formData.email}
              onChange={handleChange}
              onBlur={handleBlur}
              placeholder="operator@acme.com"
              className={`w-full h-11 px-4 rounded-xl bg-slate-950 border ${
                fieldErrors.email && touched.email ? 'border-rose-500/80 focus:border-rose-500' : 'border-slate-800 focus:border-indigo-500'
              } text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all`}
            />
            {fieldErrors.email && touched.email && (
              <p className="text-xs text-rose-400 mt-1.5 font-medium">{fieldErrors.email}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              required
              disabled={loading || Boolean(successMessage)}
              value={formData.password}
              onChange={handleChange}
              onBlur={handleBlur}
              placeholder="Minimum 8 characters"
              className={`w-full h-11 px-4 rounded-xl bg-slate-950 border ${
                fieldErrors.password && touched.password ? 'border-rose-500/80 focus:border-rose-500' : 'border-slate-800 focus:border-indigo-500'
              } text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all`}
            />
            {fieldErrors.password && touched.password && (
              <p className="text-xs text-rose-400 mt-1.5 font-medium">{fieldErrors.password}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              name="confirmPassword"
              required
              disabled={loading || Boolean(successMessage)}
              value={formData.confirmPassword}
              onChange={handleChange}
              onBlur={handleBlur}
              placeholder="Re-enter your password"
              className={`w-full h-11 px-4 rounded-xl bg-slate-950 border ${
                fieldErrors.confirmPassword && touched.confirmPassword ? 'border-rose-500/80 focus:border-rose-500' : 'border-slate-800 focus:border-indigo-500'
              } text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all`}
            />
            {fieldErrors.confirmPassword && touched.confirmPassword && (
              <p className="text-xs text-rose-400 mt-1.5 font-medium">{fieldErrors.confirmPassword}</p>
            )}
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || Boolean(successMessage)}
              className="w-full h-11 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Creating account...</span>
                </>
              ) : (
                'Create Account'
              )}
            </button>
          </div>
        </form>

        {/* Switch to Login */}
        <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
          <p className="text-xs text-slate-400">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors ml-1 underline-offset-2 hover:underline"
            >
              Login
            </Link>
          </p>
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-6 text-center text-xs text-slate-400/80 tracking-wide z-10 px-4">
        Deterministic Multi-Rail Match Engine · Immutable Ledger Guardrails
      </div>
    </div>
  )
}
