import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { loading, token } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="page-shell"><div className="card">Loading your member portal…</div></div>
  }

  if (!token) {
    return <Navigate to="/signin" replace state={{ from: location }} />
  }

  return <Outlet />
}
