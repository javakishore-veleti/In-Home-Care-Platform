export interface User {
  id: number
  email: string
  role: string
  is_active: boolean
  created_at?: string | null
}

export interface MemberProfile {
  id: number
  user_id: number
  tenant_id: string
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  dob?: string | null
  insurance_id?: string | null
  preferences: Record<string, string | boolean | number>
  created_at?: string | null
  updated_at?: string | null
}

export interface Address {
  id: number
  member_id: number
  label: string
  line1: string
  line2?: string | null
  city: string
  state: string
  postal_code: string
  instructions?: string | null
  is_default: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface Appointment {
  id: number
  member_id: number
  address_id: number
  service_type: string
  service_area?: string | null
  requested_date: string
  requested_time_slot: string
  scheduled_start?: string | null
  scheduled_end?: string | null
  reason?: string | null
  status: string
  assigned_staff_id?: number | null
  notes?: string | null
  created_at?: string | null
  updated_at?: string | null
  cancelled_at?: string | null
}

export interface AppointmentListResponse {
  items: Appointment[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Visit {
  id: number
  member_id: number
  appointment_id?: number | null
  staff_id?: number | null
  visit_date?: string | null
  status: string
  started_at?: string | null
  completed_at?: string | null
  notes_summary?: string | null
  created_at?: string | null
}

export interface VisitDocument {
  id: number
  visit_id: number
  title: string
  doc_type: string
  mime_type?: string | null
  file_path?: string | null
  summary?: string | null
  created_at?: string | null
}

export interface VisitNote {
  id: number
  visit_id: number
  note: string
  author_name?: string | null
  created_at?: string | null
}

export interface VisitDecision {
  id: number
  visit_id: number
  decision: string
  owner_name?: string | null
  created_at?: string | null
}

export interface VisitActionItem {
  id: number
  visit_id: number
  description: string
  due_date?: string | null
  status: string
  created_at?: string | null
}

export interface ChatMessage {
  id: number
  member_id: number
  role: 'user' | 'assistant'
  message: string
  created_at?: string | null
}

export interface AuthSessionResponse {
  access_token: string
  token_type: string
  expires_at: string
  user: User
  member: MemberProfile
}
