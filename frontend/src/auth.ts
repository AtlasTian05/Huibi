import { ref } from 'vue'
import { api, ApiError, post } from './api'

export const user = ref<string | null>(null)
let initialized = false

export async function loadUser(force = false) {
  if (initialized && !force) return
  try {
    const result = await api<{ username: string }>('/auth/me')
    user.value = result.username
    initialized = true
  } catch (error) {
    user.value = null
    // Network/database failures must be retried, not cached as signed out.
    initialized = error instanceof ApiError && error.status === 401
  }
}

export async function signIn(username: string, password: string) {
  const result = await post<{ username: string }>('/auth/login', {
    username,
    password,
  })
  user.value = result.username
  initialized = true
}
export async function signOut() {
  await post('/auth/logout', {})
  user.value = null
  initialized = false
}
