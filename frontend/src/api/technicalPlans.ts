import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type TechnicalPlanModule = {
  name: string
  responsibility: string
}

export type TechnicalPlanResult = {
  summary: string
  architecture_overview: string
  tech_stack: string[]
  modules: TechnicalPlanModule[]
  api_outline: string[]
  data_model_outline: string[]
  milestones: string[]
  dependencies: string[]
  risks_and_mitigations: string[]
  open_questions: string[]
}

export type TechnicalPlan = {
  id: string
  project_id: string
  requirement_analysis_id: string | null
  created_by: string
  context_text: string | null
  selected_files?: string[]
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: TechnicalPlanResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TechnicalPlanCreatePayload = {
  requirement_analysis_id?: string
  context_text?: string
  selected_files?: string[]
}

export function createTechnicalPlan(
  projectId: string,
  payload: TechnicalPlanCreatePayload,
) {
  return apiRequest<TechnicalPlan>(
    `/api/v1/projects/${projectId}/technical-plans`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listTechnicalPlans(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<TechnicalPlan>>(
    `/api/v1/projects/${projectId}/technical-plans?page=${page}&page_size=${pageSize}`,
  )
}

export function getTechnicalPlan(projectId: string, planId: string) {
  return apiRequest<TechnicalPlan>(
    `/api/v1/projects/${projectId}/technical-plans/${planId}`,
  )
}
