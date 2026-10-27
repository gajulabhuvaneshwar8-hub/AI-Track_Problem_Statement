import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import AuthLayout from './components/layout/AuthLayout'
import ProtectedRoute from './components/common/ProtectedRoute'
import LoadingSpinner from './components/common/LoadingSpinner'

// Lazy-loaded page components for optimal bundle splitting
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Transactions = lazy(() => import('./pages/Transactions'))
const Reconciliation = lazy(() => import('./pages/Reconciliation'))
const Exceptions = lazy(() => import('./pages/Exceptions'))
const AgentInvestigation = lazy(() => import('./pages/AgentInvestigation'))
const AIAnalysis = lazy(() => import('./pages/AIAnalysis'))
const DataImport = lazy(() => import('./pages/DataImport'))
const Settlements = lazy(() => import('./pages/Settlements'))
const Merchants = lazy(() => import('./pages/Merchants'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <div className="min-h-screen bg-slate-950 flex items-center justify-center">
            <LoadingSpinner message="Loading application module..." size="lg" />
          </div>
        }
      >
        <Routes>
          {/* Public authentication routes wrapped in AuthLayout */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>

          {/* Protected Control Center routes inside ProtectedRoute & AppLayout */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/reconciliation" element={<Reconciliation />} />
              <Route path="/exceptions" element={<Exceptions />} />
              <Route path="/agent" element={<AgentInvestigation />} />
              <Route path="/agent-investigation" element={<Navigate to="/agent" replace />} />
              <Route path="/ai-analysis" element={<AIAnalysis />} />
              <Route path="/import" element={<DataImport />} />
              <Route path="/settlements" element={<Settlements />} />
              <Route path="/merchants" element={<Merchants />} />
            </Route>
          </Route>

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

