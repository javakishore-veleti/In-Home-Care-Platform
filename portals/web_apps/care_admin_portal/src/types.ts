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
  updated_at?: string | null
}

export interface AppointmentRow {
  id: number
  member_id: number
  address_id: number
  service_type: string
  service_area?: string | null
  requested_date: string
  requested_time_slot: string
  status: string
  assigned_staff_id?: number | null
  notes?: string | null
  created_at?: string | null
  updated_at?: string | null
  cancelled_at?: string | null
  slack_channel_id?: string | null
  slack_message_ts?: string | null
  claimed_by_slack_user_id?: string | null
  claimed_by_slack_user_name?: string | null
  claimed_at?: string | null
}

export interface VisitRow {
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

export interface StaffRow {
  id: number
  email: string
  role: string
  is_active: boolean
  created_at?: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface DashboardStats {
  open_appointments: number
  claimed_appointments: number
  cancelled_appointments: number
  total_members: number
  todays_visits: number
}

export interface SlackIntegration {
  id: number
  slack_channel_id: string
  slack_channel_name: string
  event_type: string
  enabled: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface SlackChannelRow {
  id: string
  name: string
  is_member: boolean
  is_private: boolean
  is_archived: boolean
  integrations: SlackIntegration[]
}

export interface SlackChannelsResponse {
  channels: SlackChannelRow[]
  bot_user_id: string | null
  team: string | null
}

// ----- Knowledge Base -----

export interface KBCollection {
  id: number
  name: string
  slug: string
  service_type?: string | null
  description?: string | null
  icon_emoji: string
  org_id: string
  jurisdiction?: string | null
  repo_count: number
  total_chunks: number
  created_at?: string | null
  updated_at?: string | null
}

export interface KBRepository {
  id: number
  collection_id: number
  name: string
  slug: string
  repo_type: string
  status: string
  description?: string | null
  source_mode: string
  source_path?: string | null
  org_id: string
  jurisdictions?: string[] | null
  item_count: number
  chunk_count: number
  last_indexed_at?: string | null
  last_error?: string | null
  created_by_user_id?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface KBItem {
  id: number
  repository_id: number
  collection_id: number
  item_type: string
  title: string
  content_text?: string | null
  source_url?: string | null
  file_path?: string | null
  file_name?: string | null
  file_size_bytes?: number | null
  mime_type?: string | null
  chunk_count: number
  created_at?: string | null
}
