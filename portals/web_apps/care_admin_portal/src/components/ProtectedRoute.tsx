import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { token, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[#3D5A73]">
        Checking session...
      </div>
    )
  }
  if (!token) {
    return <Navigate to="/signin" replace state={{ from: location }} />
  }
  return <Outlet />
}
