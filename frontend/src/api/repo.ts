import { apiRequest } from './client'

export type RepoTreeEntry = {
  path: string
  name: string
  is_dir: boolean
  size: number | null
}

export type RepoTreeResponse = {
  root: string
  entries: RepoTreeEntry[]
}

export type RepoFileContent = {
  path: string
  content: string
  size: number
  truncated: boolean
}

export function getRepoTree(projectId: string, maxDepth?: number) {
  const query =
    maxDepth === undefined ? '' : `?max_depth=${encodeURIComponent(String(maxDepth))}`
  return apiRequest<RepoTreeResponse>(`/api/v1/projects/${projectId}/repo/tree${query}`)
}

export function getRepoFile(projectId: string, path: string) {
  return apiRequest<RepoFileContent>(
    `/api/v1/projects/${projectId}/repo/file?path=${encodeURIComponent(path)}`,
  )
}
