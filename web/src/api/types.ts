// Wire types for the masta HTTP API. Mirrors src/masta/api/schemas.py — change them together.

export type GoalStatus = 'active' | 'paused' | 'achieved' | 'abandoned'

export interface Health {
  status: string
  version: string
}

export interface Coach {
  name: string
  display_name: string
  description: string
  tags: string[]
  model_profile: string | null
  tools: string[]
  editable: boolean
}

export interface CoachStyle {
  both_sides: boolean
  socratic: boolean
  rest_reminders: boolean
}

export interface Guardrails {
  disclaimers: string[]
  refuse_topics: string[]
  escalate_to_professional: string[]
  safe_ranges: Record<string, number[]>
}

export interface CoachDetail extends Coach {
  persona: string
  style: CoachStyle
  guardrails: Guardrails
}

export interface CoachUpdate {
  display_name: string | null
  description: string
  tags: string[]
  model_profile: string | null
  tools: string[]
  style: CoachStyle
  guardrails: Guardrails
  persona: string
}

export interface CoachCreate extends CoachUpdate {
  name: string
}

export interface Profile {
  name: string
  model: string
  provider: string
  temperature: number
  max_tokens: number | null
  api_base: string | null
  configured: boolean
  missing_env: string[]
  is_default: boolean
  builtin: boolean
  customized: boolean
}

export interface ProfileUpdate {
  model: string
  temperature?: number
  max_tokens?: number | null
  api_base?: string | null
}

export interface Settings {
  default_profile: string
  default_profile_from_env: boolean
  config_file: string
  data_dir: string
  coaches_dir: string
}

export interface Goal {
  id: number
  title: string
  description: string
  coach: string | null
  status: GoalStatus
  created_at: string
  target_date: string | null
}

export interface GoalCreate {
  title: string
  description?: string
  coach?: string | null
}

export interface CheckIn {
  id: number
  goal_id: number | null
  note: string
  mood: number | null
  energy: number | null
  created_at: string
}

export interface CheckInCreate {
  note?: string
  goal_id?: number | null
  mood?: number | null
  energy?: number | null
}

export interface Session {
  id: number
  coach: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  coach: string | null
  session_id: number | null
  role: string
  content: string
  created_at: string
}

export interface ChatRequest {
  coach: string
  message: string
  session_id?: number | null
  profile?: string | null
}

export type ChatEvent =
  | { type: 'delta'; text: string }
  | { type: 'done' }
  | { type: 'error'; message: string }
