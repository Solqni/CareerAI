import api from '@/api'

export interface User {
  id: number
  username: string
  email: string | null
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterPayload {
  username: string
  password: string
  email?: string
  role: 'user' | 'admin'
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export async function register(payload: RegisterPayload): Promise<TokenResponse & { user: User }> {
  const { data } = await api.post<TokenResponse & { user: User }>('/auth/register', payload)
  return data
}

export async function getMe(): Promise<User> {
  try {
    const { data } = await api.get<User>('/auth/me')
    return data
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}
