import { apiRequest } from './client'

export type UserPublic = {
  id: string
  email: string
  display_name: string
  created_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  user: UserPublic
}

export function register(payload: {
  email: string
  password: string
  display_name: string
}) {
  return apiRequest<UserPublic>('/api/v1/auth/register', {
    method: 'POST',
    body: payload,
    auth: false,
  })
}

export function login(payload: { email: string; password: string }) {
  return apiRequest<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: payload,
    auth: false,
  })
}

export function fetchMe() {
  return apiRequest<UserPublic>('/api/v1/auth/me')
}
