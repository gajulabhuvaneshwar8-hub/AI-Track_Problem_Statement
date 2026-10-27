import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { authService } from '../../services/authService'

export default function ProtectedRoute({ children }) {
  const location = useLocation()
  const isAuth = authService.isAuthenticated()

  if (!isAuth) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children ? children : <Outlet />
}
