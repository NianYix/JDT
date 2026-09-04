import { apiRequest } from './client'

export type Project = {
  id: string
  owner_id: string
  name: string
  description: string | null
  repo_path: string | null
  created_at: string
  updated_at: string
}

export type PageResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export function listProjects(page = 1, pageSize = 20) {
  return apiRequest<PageResponse<Project>>(
    `/api/v1/projects?page=${page}&page_size=${pageSize}`,
  )
}

export function getProject(id: string) {
  return apiRequest<Project>(`/api/v1/projects/${id}`)
}

export function createProject(payload: {
  name: string
  description?: string
  repo_path?: string
}) {
  return apiRequest<Project>('/api/v1/projects', {
    method: 'POST',
    body: payload,
  })
}

export function updateProject(
  id: string,
  payload: { name?: string; description?: string | null; repo_path?: string | null },
) {
  return apiRequest<Project>(`/api/v1/projects/${id}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function deleteProject(id: string) {
  return apiRequest<void>(`/api/v1/projects/${id}`, {
    method: 'DELETE',
  })
}
