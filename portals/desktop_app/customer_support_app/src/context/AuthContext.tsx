import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'

import { api } from '../lib/api'
import type { User } from '../types'

const STORAGE_KEY = 'support-app-auth-token'
const ALLOWED_ROLES = new Set(['support', 'admin'])

interface AuthContextValue {
  token: string | null
  user: User | null
  loading: boolean
  signin: (payload: { email: string; password: string }) => Promise<void>
  signout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const clearSession = useCallback(() => {
    setToken(null)
    setUser(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function refresh() {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await api.me(token)
        if (!cancelled) setUser(me.user)
      } catch {
        if (!cancelled) clearSession()
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void refresh()
    return () => {
      cancelled = true
    }
  }, [token, clearSession])

  const signin = useCallback(async (payload: { email: string; password: string }) => {
    const session = await api.signin(payload)
    if (!ALLOWED_ROLES.has(session.user.role)) {
      throw new Error('Your account does not have customer-support access. Sign in to the appropriate portal instead.')
    }
    localStorage.setItem(STORAGE_KEY, session.access_token)
    setToken(session.access_token)
    setUser(session.user)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, loading, signin, signout: clearSession }),
    [token, user, loading, signin, clearSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
