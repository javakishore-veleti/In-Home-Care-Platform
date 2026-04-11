import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function SignInPage() {
  const { token, signin, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation() as { state?: { from?: { pathname?: string } } }
  const [email, setEmail] = useState('admin01@inhomecare.local')
  const [password, setPassword] = useState('Admin@123')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-[#3D5A73]">Checking session...</div>
  }
  if (token) {
    return <Navigate to={location.state?.from?.pathname ?? '/app'} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await signin({ email, password })
      navigate(location.state?.from?.pathname ?? '/app', { replace: true })
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Sign in failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F4F7FA] px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8 border border-[#0D7377]/10"
      >
        <div className="flex items-center gap-3 mb-6">
          <img src="/logo.svg" alt="Logo" className="h-10 w-10" />
          <div>
            <h1 className="text-lg font-bold text-[#1A2B3C]">Care Admin Portal</h1>
            <p className="text-xs text-[#3D5A73]">Internal sign-in</p>
          </div>
        </div>
        <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          required
          className="w-full mb-4 px-3 py-2 rounded border border-[#0D7377]/20 focus:outline-none focus:ring-2 focus:ring-[#0D7377] text-sm"
        />
        <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Password</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          required
          className="w-full mb-4 px-3 py-2 rounded border border-[#0D7377]/20 focus:outline-none focus:ring-2 focus:ring-[#0D7377] text-sm"
        />
        {error && (
          <div className="mb-4 text-xs text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-[#0D7377] hover:bg-[#084C4F] text-white font-semibold py-2 rounded text-sm disabled:opacity-60"
        >
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
        <p className="mt-4 text-[10px] text-[#3D5A73] leading-snug">
          Default admin credential for local dev: <code>admin01@inhomecare.local</code> / <code>Admin@123</code>.
          Internal-staff users are seeded automatically by auth_svc on startup.
        </p>
      </form>
    </div>
  )
}
