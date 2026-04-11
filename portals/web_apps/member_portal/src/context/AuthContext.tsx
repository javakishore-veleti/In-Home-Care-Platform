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
import type { AuthSessionResponse, MemberProfile, User } from '../types'

const STORAGE_KEY = 'member-portal-auth-token'

interface AuthContextValue {
  token: string | null
  user: User | null
  member: MemberProfile | null
  loading: boolean
  signin: (payload: { email: string; password: string }) => Promise<void>
  signup: (payload: { email: string; password: string; first_name: string; last_name: string; phone: string }) => Promise<void>
  signout: () => void
  refreshSession: () => Promise<void>
  setSessionState: (session: { user: User; member: MemberProfile }) => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function persistSession(session: AuthSessionResponse) {
  localStorage.setItem(STORAGE_KEY, session.access_token)
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [member, setMember] = useState<MemberProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const clearSession = useCallback(() => {
    setToken(null)
    setUser(null)
    setMember(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const refreshSession = useCallback(async () => {
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const response = await api.me(token)
      setUser(response.user)
      setMember(response.member)
    } catch {
      clearSession()
    } finally {
      setLoading(false)
    }
  }, [clearSession, token])

  useEffect(() => {
    void refreshSession()
  }, [refreshSession])

  const signin = useCallback(async (payload: { email: string; password: string }) => {
    const session = await api.signin(payload)
    persistSession(session)
    setToken(session.access_token)
    setUser(session.user)
    setMember(session.member)
  }, [])

  const signup = useCallback(
    async (payload: { email: string; password: string; first_name: string; last_name: string; phone: string }) => {
      await api.signup(payload)
      await signin({ email: payload.email, password: payload.password })
    },
    [signin],
  )

  const value = useMemo<AuthContextValue>(() => ({
    token,
    user,
    member,
    loading,
    signin,
    signup,
    signout: clearSession,
    refreshSession,
    setSessionState: (session) => {
      setUser(session.user)
      setMember(session.member)
    },
  }), [clearSession, loading, member, refreshSession, signin, signup, token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
