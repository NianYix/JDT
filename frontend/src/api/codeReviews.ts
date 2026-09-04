import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type IssueItem = {
  severity: string
  location: string
  category: string
  description: string
  suggestion: string
}

export type FixSuggestion = {
  path: string
  description: string
  content: string
}

export type ReviewResult = {
  summary: string
  overall_assessment: string
  issues: IssueItem[]
  strengths: string[]
  security_notes: string[]
  performance_notes: string[]
  maintainability_notes: string[]
  suggested_fixes: FixSuggestion[]
  open_questions: string[]
}

export type CodeReview = {
  id: string
  project_id: string
  code_generation_id: string | null
  created_by: string
  review_scope: string
  context_text: string | null
  selected_files?: string[]
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: ReviewResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type CodeReviewCreatePayload = {
  code_generation_id?: string
  review_scope: string
  context_text?: string
  selected_files?: string[]
}

export function createCodeReview(projectId: string, payload: CodeReviewCreatePayload) {
  return apiRequest<CodeReview>(
    `/api/v1/projects/${projectId}/code-reviews`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listCodeReviews(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<CodeReview>>(
    `/api/v1/projects/${projectId}/code-reviews?page=${page}&page_size=${pageSize}`,
  )
}

export function getCodeReview(projectId: string, reviewId: string) {
  return apiRequest<CodeReview>(
    `/api/v1/projects/${projectId}/code-reviews/${reviewId}`,
  )
}
