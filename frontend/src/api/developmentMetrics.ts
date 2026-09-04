import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type WorkflowCoverageItem = {
  stage: string
  status: string
  notes: string
}

export type QualityIndicatorItem = {
  name: string
  assessment: string
  evidence: string
}

export type MetricsReportResult = {
  summary: string
  overall_health: string
  workflow_coverage: WorkflowCoverageItem[]
  quality_indicators: QualityIndicatorItem[]
  velocity_indicators: string[]
  risk_indicators: string[]
  recommendations: string[]
  open_questions: string[]
}

export type DevelopmentMetric = {
  id: string
  project_id: string
  created_by: string
  metrics_focus: string
  context_text: string | null
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: MetricsReportResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type DevelopmentMetricCreatePayload = {
  metrics_focus: string
  context_text?: string
}

export function createDevelopmentMetric(
  projectId: string,
  payload: DevelopmentMetricCreatePayload,
) {
  return apiRequest<DevelopmentMetric>(
    `/api/v1/projects/${projectId}/development-metrics`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listDevelopmentMetrics(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<DevelopmentMetric>>(
    `/api/v1/projects/${projectId}/development-metrics?page=${page}&page_size=${pageSize}`,
  )
}

export function getDevelopmentMetric(projectId: string, metricId: string) {
  return apiRequest<DevelopmentMetric>(
    `/api/v1/projects/${projectId}/development-metrics/${metricId}`,
  )
}
