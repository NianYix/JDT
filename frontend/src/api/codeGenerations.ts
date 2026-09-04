import { apiRequest } from './client'
import type { PageResponse } from './projects'

export type CodeGenerationFile = {
  path: string
  language: string
  description: string
  content: string
}

export type CodeGenerationResult = {
  summary: string
  approach: string
  files: CodeGenerationFile[]
  dependencies: string[]
  implementation_steps: string[]
  testing_notes: string[]
  risks: string[]
  open_questions: string[]
}

export type CodeGeneration = {
  id: string
  project_id: string
  technical_plan_id: string | null
  created_by: string
  task_description: string
  context_text: string | null
  selected_files?: string[]
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  result_json: CodeGenerationResult | null
  model_name: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type CodeGenerationCreatePayload = {
  technical_plan_id?: string
  task_description: string
  context_text?: string
  selected_files?: string[]
}

export function createCodeGeneration(
  projectId: string,
  payload: CodeGenerationCreatePayload,
) {
  return apiRequest<CodeGeneration>(
    `/api/v1/projects/${projectId}/code-generations`,
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function listCodeGenerations(projectId: string, page = 1, pageSize = 20) {
  return apiRequest<PageResponse<CodeGeneration>>(
    `/api/v1/projects/${projectId}/code-generations?page=${page}&page_size=${pageSize}`,
  )
}

export function getCodeGeneration(projectId: string, generationId: string) {
  return apiRequest<CodeGeneration>(
    `/api/v1/projects/${projectId}/code-generations/${generationId}`,
  )
}
