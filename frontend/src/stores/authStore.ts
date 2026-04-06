import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const TOKEN_LIFETIME_MS = 24 * 60 * 60 * 1000 // 24h
const REFRESH_THRESHOLD_MS = 60 * 60 * 1000 // 剩不到 1 小時就 refresh
const REFRESH_CHECK_INTERVAL_MS = 10 * 60 * 1000 // 每 10 分鐘檢查
const IDLE_TIMEOUT_MS = 30 * 60 * 1000 // 閒置 30 分鐘自動登出

const IDLE_EVENTS = ['mousedown', 'keydown', 'touchstart', 'scroll'] as const

export interface AuthUser {
  id: number
  username: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<AuthUser | null>(null)
  const tokenExpiresAt = ref<number>(
    Number(localStorage.getItem('auth_token_expires_at') || '0'),
  )

  let refreshInterval: ReturnType<typeof setInterval> | null = null
  let idleTimer: ReturnType<typeof setTimeout> | null = null
  let idleListenersAttached = false

  const isLoggedIn = computed(() => !!token.value)

  function getAuthHeaders(): Record<string, string> {
    if (!token.value) return {}
    return { Authorization: `Token ${token.value}` }
  }

  function setExpiresAt(ts: number) {
    tokenExpiresAt.value = ts
    localStorage.setItem('auth_token_expires_at', String(ts))
  }

  function clearExpiresAt() {
    tokenExpiresAt.value = 0
    localStorage.removeItem('auth_token_expires_at')
  }

  async function register(
    username: string,
    password: string,
    passwordConfirm: string,
    email?: string,
  ) {
    const body: Record<string, string> = { username, password, password_confirm: passwordConfirm }
    if (email) body.email = email

    const res = await fetch(`${API_BASE}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const data = await res.json()
    if (!res.ok) {
      const msg = extractError(data)
      throw new Error(msg)
    }

    token.value = data.token
    localStorage.setItem('auth_token', data.token)
    setExpiresAt(Date.now() + TOKEN_LIFETIME_MS)
    user.value = data.user ?? { id: data.id, username: data.username, email: data.email ?? '' }
    startSessionTimers()
  }

  async function login(username: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    const data = await res.json()
    if (!res.ok) {
      const msg = extractError(data)
      throw new Error(msg)
    }

    token.value = data.token
    localStorage.setItem('auth_token', data.token)
    setExpiresAt(Date.now() + TOKEN_LIFETIME_MS)
    user.value = data.user ?? { id: data.id, username: data.username, email: data.email ?? '' }
    startSessionTimers()
  }

  async function logout() {
    try {
      await fetch(`${API_BASE}/auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      })
    } catch {
      // ignore network errors on logout
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      clearExpiresAt()
      stopSessionTimers()
    }
  }

  async function refreshToken(): Promise<boolean> {
    if (!token.value) return false
    try {
      const res = await fetch(`${API_BASE}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      })
      if (!res.ok) return false
      const data = await res.json()
      token.value = data.token
      localStorage.setItem('auth_token', data.token)
      setExpiresAt(Date.now() + TOKEN_LIFETIME_MS)
      if (data.user) {
        user.value = { id: data.user.id, username: data.user.username, email: data.user.email ?? '' }
      }
      return true
    } catch {
      return false
    }
  }

  async function fetchProfile() {
    if (!token.value) return
    const res = await fetch(`${API_BASE}/auth/profile/`, {
      headers: { ...getAuthHeaders() },
    })
    if (!res.ok) {
      // token invalid
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      clearExpiresAt()
      stopSessionTimers()
      return
    }
    const data = await res.json()
    user.value = { id: data.id, username: data.username, email: data.email ?? '' }
  }

  // -------------------- Session timers --------------------

  function startSessionTimers() {
    startRefreshInterval()
    attachIdleListeners()
    resetIdleTimer()
  }

  function stopSessionTimers() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
    if (idleTimer) {
      clearTimeout(idleTimer)
      idleTimer = null
    }
    detachIdleListeners()
  }

  function startRefreshInterval() {
    if (refreshInterval) clearInterval(refreshInterval)
    refreshInterval = setInterval(() => {
      if (!token.value) return
      const remaining = tokenExpiresAt.value - Date.now()
      if (remaining > 0 && remaining < REFRESH_THRESHOLD_MS) {
        refreshToken()
      }
    }, REFRESH_CHECK_INTERVAL_MS)
  }

  function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer)
    idleTimer = setTimeout(async () => {
      if (!token.value) return
      await logout()
      try {
        window.alert('因閒置時間過久，已自動登出。')
      } catch {
        // ignore
      }
      if (typeof window !== 'undefined' && window.location) {
        window.location.href = '/login'
      }
    }, IDLE_TIMEOUT_MS)
  }

  function onUserActivity() {
    if (token.value) resetIdleTimer()
  }

  function attachIdleListeners() {
    if (idleListenersAttached || typeof window === 'undefined') return
    IDLE_EVENTS.forEach((evt) => {
      window.addEventListener(evt, onUserActivity, { passive: true })
    })
    idleListenersAttached = true
  }

  function detachIdleListeners() {
    if (!idleListenersAttached || typeof window === 'undefined') return
    IDLE_EVENTS.forEach((evt) => {
      window.removeEventListener(evt, onUserActivity)
    })
    idleListenersAttached = false
  }

  // 重新載入頁面時若已有 token，恢復計時器
  function initSession() {
    if (token.value) {
      if (!tokenExpiresAt.value) {
        setExpiresAt(Date.now() + TOKEN_LIFETIME_MS)
      }
      startSessionTimers()
    }
  }

  function extractError(data: any): string {
    if (typeof data === 'string') return data
    if (data.detail) return data.detail
    if (data.non_field_errors) return data.non_field_errors.join(', ')
    if (data.error) return data.error
    const messages: string[] = []
    for (const key of Object.keys(data)) {
      const val = data[key]
      if (Array.isArray(val)) {
        messages.push(`${key}: ${val.join(', ')}`)
      } else if (typeof val === 'string') {
        messages.push(val)
      }
    }
    return messages.length > 0 ? messages.join('; ') : '操作失敗'
  }

  return {
    token,
    user,
    tokenExpiresAt,
    isLoggedIn,
    getAuthHeaders,
    register,
    login,
    logout,
    refreshToken,
    fetchProfile,
    initSession,
  }
})
