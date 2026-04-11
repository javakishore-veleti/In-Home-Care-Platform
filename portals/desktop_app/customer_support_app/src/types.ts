export interface User {
  id: number
  email: string
  role: string
  is_active: boolean
  created_at?: string | null
}

export interface AuthSessionResponse {
  access_token: string
  token_type: string
  expires_at: string
  user: User
  member?: unknown | null
}

export interface MemberRow {
  id: number
  user_id: number
  tenant_id: string
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  dob?: string | null
  insurance_id?: string | null
  created_at?: string | null
}

export interface AppointmentRow {
  id: number
  member_id: number
  service_type: string
  service_area?: string | null
  requested_date: string
  requested_time_slot: string
  status: string
  notes?: string | null
  claimed_by_slack_user_name?: string | null
  claimed_by_slack_user_id?: string | null
  claimed_at?: string | null
}

export interface VisitRow {
  id: number
  member_id: number
  appointment_id?: number | null
  visit_date?: string | null
  status: string
  notes_summary?: string | null
}

export interface CaseRow {
  id: number
  member_id: number
  subject: string
  description?: string | null
  priority: string
  status: string
  created_by_user_id?: number | null
  assigned_to_user_id?: number | null
  created_at?: string | null
  updated_at?: string | null
  resolved_at?: string | null
}

export interface SupportCaseCreate {
  member_id: number
  subject: string
  description?: string
  priority: string
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}
