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

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export async function register(
  username: string,
  password: string,
  email?: string,
): Promise<User> {
  const { data } = await api.post<User>('/auth/register', { username, password, email })
  return data
}
