import type {
  AppointmentRow,
  AuthSessionResponse,
  DashboardStats,
  MemberRow,
  PaginatedResponse,
  StaffRow,
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
  dashboardStats(token: string) {
    return request<DashboardStats>('/api/admin/dashboard/stats', {}, token)
  },
  listMembers(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<MemberRow>>(`/api/admin/members?${params.toString()}`, {}, token)
  },
  listAppointments(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<AppointmentRow>>(`/api/admin/appointments?${params.toString()}`, {}, token)
  },
  getAppointment(token: string, appointmentId: number) {
    return request<AppointmentRow>(`/api/admin/appointments/${appointmentId}`, {}, token)
  },
  listVisits(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<VisitRow>>(`/api/admin/visits?${params.toString()}`, {}, token)
  },
  getVisit(token: string, visitId: number) {
    return request<VisitRow>(`/api/admin/visits/${visitId}`, {}, token)
  },
  listClaims(token: string, params: URLSearchParams) {
    return request<PaginatedResponse<AppointmentRow>>(`/api/admin/claims?${params.toString()}`, {}, token)
  },
  listStaff(token: string) {
    return request<{ items: StaffRow[]; total: number }>('/api/admin/staff', {}, token)
  },
  getMember(token: string, memberId: number) {
    return request<MemberRow>(`/api/admin/members/${memberId}`, {}, token)
  },
}
