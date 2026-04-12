import type {
  AppointmentRow,
  AuthSessionResponse,
  ChunkRow,
  DashboardStats,
  IndexingRun,
  KBCollection,
  KBItem,
  KBRepository,
  MemberRow,
  PaginatedResponse,
  SlackChannelsResponse,
  SlackIntegration,
  StaffRow,
  User,
  VectorDBOption,
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
  // ----- Slack integrations -----
  listSlackChannels(token: string) {
    return request<SlackChannelsResponse>('/api/admin/slack/channels', {}, token)
  },
  inviteBotToChannel(token: string, channelId: string) {
    return request<{ ok: boolean; error?: string }>(`/api/admin/slack/channels/${channelId}/invite`, {
      method: 'POST',
    }, token)
  },
  upsertSlackIntegration(
    token: string,
    payload: { slack_channel_id: string; slack_channel_name: string; event_type: string },
  ) {
    return request<SlackIntegration>('/api/admin/slack/integrations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
  toggleSlackIntegration(token: string, integrationId: number, enabled: boolean) {
    return request<SlackIntegration>(`/api/admin/slack/integrations/${integrationId}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    }, token)
  },
  deleteSlackIntegration(token: string, integrationId: number) {
    return request<void>(`/api/admin/slack/integrations/${integrationId}`, {
      method: 'DELETE',
    }, token)
  },
  // ----- Knowledge Base -----
  listKBCollections(token: string) {
    return request<{ items: KBCollection[]; total: number }>('/api/admin/knowledge/collections', {}, token)
  },
  getKBCollection(token: string, id: number) {
    return request<KBCollection>(`/api/admin/knowledge/collections/${id}`, {}, token)
  },
  listKBRepositories(token: string, collectionId: number) {
    return request<{ items: KBRepository[]; total: number }>(`/api/admin/knowledge/collections/${collectionId}/repositories`, {}, token)
  },
  getKBRepository(token: string, repoId: number) {
    return request<KBRepository>(`/api/admin/knowledge/repositories/${repoId}`, {}, token)
  },
  createKBRepository(token: string, collectionId: number, payload: Record<string, unknown>) {
    return request<KBRepository>(`/api/admin/knowledge/collections/${collectionId}/repositories`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
  lockKBRepository(token: string, repoId: number) {
    return request<KBRepository>(`/api/admin/knowledge/repositories/${repoId}/lock`, { method: 'POST' }, token)
  },
  unlockKBRepository(token: string, repoId: number) {
    return request<KBRepository>(`/api/admin/knowledge/repositories/${repoId}/unlock`, { method: 'POST' }, token)
  },
  publishKBRepository(token: string, repoId: number) {
    return request<KBRepository>(`/api/admin/knowledge/repositories/${repoId}/publish`, { method: 'POST' }, token)
  },
  updateKBTargetVectorDBs(token: string, repoId: number, targets: string[]) {
    return request<KBRepository>(`/api/admin/knowledge/repositories/${repoId}/target-vectordbs`, {
      method: 'PATCH',
      body: JSON.stringify({ target_vectordbs: targets }),
    }, token)
  },
  listKBIndexingHistory(token: string, repoId: number, params: URLSearchParams) {
    return request<PaginatedResponse<IndexingRun>>(`/api/admin/knowledge/repositories/${repoId}/indexing-history?${params.toString()}`, {}, token)
  },
  listSupportedVectorDBs(token: string) {
    return request<{ items: VectorDBOption[] }>('/api/admin/knowledge/supported-vectordbs', {}, token)
  },
  searchKnowledge(token: string, payload: {
    query: string
    collection_id?: number
    collection_slug?: string
    top_k?: number
    strategy_filter?: string
  }) {
    return request<{ query: string; results: ChunkRow[]; total: number }>(
      '/api/admin/knowledge/search',
      { method: 'POST', body: JSON.stringify(payload) },
      token,
    )
  },
  getKBIndexingRun(token: string, runId: number) {
    return request<IndexingRun>(`/api/admin/knowledge/indexing-runs/${runId}`, {}, token)
  },
  listKBChunks(token: string, repoId: number, params: URLSearchParams) {
    return request<PaginatedResponse<ChunkRow>>(`/api/admin/knowledge/repositories/${repoId}/chunks?${params.toString()}`, {}, token)
  },
  listKBItems(token: string, repoId: number) {
    return request<{ items: KBItem[]; total: number }>(`/api/admin/knowledge/repositories/${repoId}/items`, {}, token)
  },
  createKBItem(token: string, repoId: number, payload: Record<string, unknown>) {
    return request<KBItem>(`/api/admin/knowledge/repositories/${repoId}/items`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)
  },
  async uploadKBFile(token: string, repoId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const headers = new Headers()
    headers.set('Authorization', `Bearer ${token}`)
    const resp = await fetch(`${API_BASE_URL}/api/admin/knowledge/repositories/${repoId}/items/upload`, {
      method: 'POST',
      headers,
      body: formData,
    })
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) throw new ApiError(data.detail ?? 'Upload failed.', resp.status)
    return data as KBItem
  },
  deleteKBItem(token: string, itemId: number) {
    return request<void>(`/api/admin/knowledge/items/${itemId}`, { method: 'DELETE' }, token)
  },
  setupKBDefaults(token: string) {
    return request<{ status: string; job?: Record<string, unknown> }>('/api/admin/knowledge/setup-defaults', { method: 'POST' }, token)
  },
  getKBSetupStatus(token: string) {
    return request<{ job: Record<string, unknown> | null }>('/api/admin/knowledge/setup-defaults/status', {}, token)
  },
  resetKBSetup(token: string) {
    return request<{ status: string }>('/api/admin/knowledge/setup-defaults/reset', { method: 'POST' }, token)
  },
}
