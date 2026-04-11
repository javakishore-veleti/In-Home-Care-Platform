import type {
  AppointmentRow,
  AuthSessionResponse,
  CaseRow,
  MemberRow,
  PaginatedResponse,
  User,
  VisitRow,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(data.detail ?? 'Request failed.', response.status)
  }
  return data as T
}

export const api = {
  signin(payload: { email: string; password: string }) {
    return request<AuthSessionResponse>('/api/auth/signin', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  me(token: string) {
    return request<{ user: User; member: unknown }>('/api/auth/me', {}, token)
  },
  listCases(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<CaseRow>>(`/api/support/cases?${params.toString()}`, {}, token)
  },
  listMembers(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<MemberRow>>(`/api/support/members?${params.toString()}`, {}, token)
  },
  listAppointments(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<AppointmentRow>>(`/api/support/appointments?${params.toString()}`, {}, token)
  },
  listVisits(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<VisitRow>>(`/api/support/visits?${params.toString()}`, {}, token)
  },
}
