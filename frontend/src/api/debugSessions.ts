import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type LikelyCauseItem = {
  hypothesis: string
  confidence: string
  evidence: string
}

export type DebugFixItem = {
  description: string
  content: string
}

export type DebugAnalysisResult = {
  summary: string
  root_cause_analysis: string
  likely_causes: LikelyCauseItem[]
  debugging_steps: string[]
  fix_suggestions: DebugFixItem[]
  verification_steps: string[]
  prevention_notes: string[]
  open_questions: string[]
}

export type DebugSession = {
  id: string
  project_id: string
  code_review_id: string | null
  code_generation_id: string | null
  created_by: string
  problem_description: string
  context_text: string | null
  selected_files?: string[]
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: DebugAnalysisResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type DebugSessionCreatePayload = {
  code_review_id?: string
  code_generation_id?: string
  problem_description: string
  context_text?: string
  selected_files?: string[]
}

export function createDebugSession(projectId: string, payload: DebugSessionCreatePayload) {
  return apiRequest<DebugSession>(
    `/api/v1/projects/${projectId}/debug-sessions`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listDebugSessions(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<DebugSession>>(
    `/api/v1/projects/${projectId}/debug-sessions?page=${page}&page_size=${pageSize}`,
  )
}

export function getDebugSession(projectId: string, sessionId: string) {
  return apiRequest<DebugSession>(
    `/api/v1/projects/${projectId}/debug-sessions/${sessionId}`,
  )
}
