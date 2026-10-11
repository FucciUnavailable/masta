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
}

export interface Profile {
  name: string
  model: string
  provider: string
  configured: boolean
  is_default: boolean
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

export interface Message {
  id: number
  coach: string | null
  role: string
  content: string
  created_at: string
}

export interface ChatRequest {
  coach: string
  message: string
  profile?: string | null
}

export type ChatEvent =
  | { type: 'delta'; text: string }
  | { type: 'done' }
  | { type: 'error'; message: string }
