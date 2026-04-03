import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export interface AuthUser {
  id: number
  username: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<AuthUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function getAuthHeaders(): Record<string, string> {
    if (!token.value) return {}
    return { 'Authorization': `Token ${token.value}` }
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
    user.value = data.user ?? { id: data.id, username: data.username, email: data.email ?? '' }
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
    user.value = data.user ?? { id: data.id, username: data.username, email: data.email ?? '' }
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
      return
    }
    const data = await res.json()
    user.value = { id: data.id, username: data.username, email: data.email ?? '' }
  }

  function extractError(data: any): string {
    if (typeof data === 'string') return data
    if (data.detail) return data.detail
    if (data.non_field_errors) return data.non_field_errors.join(', ')
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
    isLoggedIn,
    getAuthHeaders,
    register,
    login,
    logout,
    fetchProfile,
  }
})
