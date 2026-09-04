import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import * as authApi from '../api/auth'
import type { UserPublic } from '../api/auth'
import { getStoredToken, setStoredToken } from '../api/client'

type AuthContextValue = {
  user: UserPublic | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [loading, setLoading] = useState(true)

  const refreshMe = useCallback(async () => {
    const current = getStoredToken()
    if (!current) {
      setUser(null)
      setToken(null)
      return
    }
    const me = await authApi.fetchMe()
    setUser(me)
    setToken(current)
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (getStoredToken()) {
          await refreshMe()
        }
      } catch {
        setStoredToken(null)
        if (!cancelled) {
          setUser(null)
          setToken(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refreshMe])

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login({ email, password })
    setStoredToken(result.access_token)
    setToken(result.access_token)
    setUser(result.user)
  }, [])

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      await authApi.register({
        email,
        password,
        display_name: displayName,
      })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout, refreshMe }),
    [user, token, loading, login, register, logout, refreshMe],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
