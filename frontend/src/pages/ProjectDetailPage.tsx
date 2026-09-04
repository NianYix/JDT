import { useEffect, useState } from 'react'
import { Typography, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import * as projectsApi from '../api/projects'
import type { Project } from '../api/projects'
import { ApiError } from '../api/client'
import { ProjectWorkspace } from '../workspace/ProjectWorkspace'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)

  useEffect(() => {
    if (!id) return
    ;(async () => {
      try {
        const data = await projectsApi.getProject(id)
        setProject(data)
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
        navigate('/projects')
      }
    })()
  }, [id, navigate])

  if (!project) {
    return (
      <div className="main-pane-padded">
        <Typography.Text type="secondary">加载中…</Typography.Text>
      </div>
    )
  }

  return <ProjectWorkspace project={project} />
}
