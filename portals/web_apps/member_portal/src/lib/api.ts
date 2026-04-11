import type {
  Address,
  AddressListResponse,
  Appointment,
  AppointmentListResponse,
  AuthSessionResponse,
  ChatMessage,
  MemberProfile,
  User,
  Visit,
  VisitActionItem,
  VisitDecision,
  VisitDocument,
  VisitNote,
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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(data.detail ?? 'Something went wrong.', response.status)
  }
  return data as T
}

export const api = {
  signup(payload: Record<string, unknown>) {
    return request<{ user: User; member: MemberProfile }>('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  signin(payload: Record<string, unknown>) {
    return request<AuthSessionResponse>('/api/auth/signin', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  me(token: string) {
    return request<{ user: User; member: MemberProfile }>('/api/auth/me', {}, token)
  },
  getProfile(token: string) {
    return request<MemberProfile>('/api/member/profile', {}, token)
  },
  updateProfile(token: string, payload: Record<string, unknown>) {
    return request<MemberProfile>('/api/member/profile', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }, token)
  },
  listAddresses(token: string) {
    return request<Address[]>('/api/member/addresses', {}, token)
  },
  searchAddresses(token: string, params: URLSearchParams) {
    return request<AddressListResponse>(`/api/member/address-directory?${params.toString()}`, {}, token)
  },
  createAddress(token: string, payload: Record<string, unknown>) {
    return request<Address>('/api/member/addresses', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
  updateAddress(token: string, addressId: number, payload: Record<string, unknown>) {
    return request<Address>(`/api/member/addresses/${addressId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }, token)
  },
  deleteAddress(token: string, addressId: number) {
    return request<void>(`/api/member/addresses/${addressId}`, { method: 'DELETE' }, token)
  },
  setDefaultAddress(token: string, addressId: number) {
    return request<Address>(`/api/member/addresses/${addressId}/default`, { method: 'PATCH' }, token)
  },
  createAppointment(token: string, payload: Record<string, unknown>) {
    return request<Appointment>('/api/member/appointments', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
  listAppointments(token: string, params: URLSearchParams) {
    return request<AppointmentListResponse>(`/api/member/appointments?${params.toString()}`, {}, token)
  },
  getAppointment(token: string, appointmentId: number) {
    return request<Appointment>(`/api/member/appointments/${appointmentId}`, {}, token)
  },
  updateAppointment(token: string, appointmentId: number, payload: Record<string, unknown>) {
    return request<Appointment>(`/api/member/appointments/${appointmentId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }, token)
  },
  cancelAppointment(token: string, appointmentId: number) {
    return request<Appointment>(`/api/member/appointments/${appointmentId}/cancel`, { method: 'POST' }, token)
  },
  listAppointmentVisits(token: string, appointmentId: number) {
    return request<Visit[]>(`/api/member/appointments/${appointmentId}/visits`, {}, token)
  },
  getVisit(token: string, visitId: number) {
    return request<Visit>(`/api/member/visits/${visitId}`, {}, token)
  },
  listVisitDocuments(token: string, visitId: number) {
    return request<VisitDocument[]>(`/api/member/visits/${visitId}/documents`, {}, token)
  },
  listVisitNotes(token: string, visitId: number) {
    return request<VisitNote[]>(`/api/member/visits/${visitId}/notes`, {}, token)
  },
  listVisitDecisions(token: string, visitId: number) {
    return request<VisitDecision[]>(`/api/member/visits/${visitId}/decisions`, {}, token)
  },
  listVisitActionItems(token: string, visitId: number) {
    return request<VisitActionItem[]>(`/api/member/visits/${visitId}/action-items`, {}, token)
  },
  listChatMessages(token: string) {
    return request<{ messages: ChatMessage[] }>('/api/member/chat/messages', {}, token)
  },
  sendChatMessage(token: string, payload: Record<string, unknown>) {
    return request<{ messages: ChatMessage[] }>('/api/member/chat/messages', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
}
