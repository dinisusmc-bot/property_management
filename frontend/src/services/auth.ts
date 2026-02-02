import api from './api'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export const authService = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await api.post<LoginResponse>('/api/v1/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  getCurrentUser: async (token?: string): Promise<User> => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const response = await api.get<User>('/api/v1/auth/me', { headers })
    return response.data
  },

  register: async (data: {
    email: string
    full_name: string
    password: string
  }): Promise<User> => {
    const response = await api.post<User>('/api/v1/auth/register', data)
    return response.data
  },
}
