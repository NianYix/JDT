import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type TestCaseItem = {
  name: string
  type: string
  description: string
  steps: string[]
  expected: string
}

export type TestFileItem = {
  path: string
  language: string
  description: string
  content: string
}

export type TestGenerationResult = {
  summary: string
  testing_strategy: string
  test_cases: TestCaseItem[]
  test_files: TestFileItem[]
  fixtures_and_mocks: string[]
  coverage_notes: string[]
  risks: string[]
  open_questions: string[]
}

export type TestGeneration = {
  id: string
  project_id: string
  code_generation_id: string | null
  created_by: string
  target_description: string
  context_text: string | null
  selected_files?: string[]
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: TestGenerationResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TestGenerationCreatePayload = {
  code_generation_id?: string
  target_description: string
  context_text?: string
  selected_files?: string[]
}

export function createTestGeneration(
  projectId: string,
  payload: TestGenerationCreatePayload,
) {
  return apiRequest<TestGeneration>(
    `/api/v1/projects/${projectId}/test-generations`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listTestGenerations(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<TestGeneration>>(
    `/api/v1/projects/${projectId}/test-generations?page=${page}&page_size=${pageSize}`,
  )
}

export function getTestGeneration(projectId: string, generationId: string) {
  return apiRequest<TestGeneration>(
    `/api/v1/projects/${projectId}/test-generations/${generationId}`,
  )
}
