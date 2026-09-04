import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type RequirementAnalysisResult = {
  summary: string
  goals: string[]
  stakeholders: string[]
  functional_requirements: string[]
  non_functional_requirements: string[]
  assumptions: string[]
  risks: string[]
  open_questions: string[]
}

export type RequirementAnalysis = {
  id: string
  project_id: string
  created_by: string
  source_text: string
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: RequirementAnalysisResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export function createRequirementAnalysis(projectId: string, sourceText: string) {
  return apiRequest<RequirementAnalysis>(
    `/api/v1/projects/${projectId}/requirement-analyses`,
    {
      method: 'POST',
      body: { source_text: sourceText },
    },
  )
}

export function listRequirementAnalyses(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<RequirementAnalysis>>(
    `/api/v1/projects/${projectId}/requirement-analyses?page=${page}&page_size=${pageSize}`,
  )
}

export function getRequirementAnalysis(projectId: string, analysisId: string) {
  return apiRequest<RequirementAnalysis>(
    `/api/v1/projects/${projectId}/requirement-analyses/${analysisId}`,
  )
}
