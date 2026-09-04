import { Link } from 'react-router-dom'
import { Typography } from 'antd'
import type { ReactNode } from 'react'
import { StatusDot } from '../components/workflow/StatusDot'
import { AgentControlPanel } from './AgentControlPanel'
import { getStage, type StageId } from './stages'
import { toVisualStatus, visualLabel, type WorkflowStatus } from './statusMap'

type Props = {
  stageId: StageId
  status: WorkflowStatus | 'idle'
  errorMessage?: string | null
  children: ReactNode
}

export function InspectorPanel({ stageId, status, errorMessage, children }: Props) {
  const stage = getStage(stageId)
  const visual = toVisualStatus(status)

  return (
    <aside className="inspector-panel">
      <div className="inspector-header">
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Typography.Text strong style={{ color: 'var(--text)' }}>
              {stage.title}
            </Typography.Text>
            <span className="mono" style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
              {stage.nodeId}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <StatusDot visual={visual} />
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {visualLabel(visual)}
            </span>
          </div>
        </div>
        <Link to="/projects" style={{ fontSize: 12 }}>
          ← 列表
        </Link>
      </div>
      <div className="inspector-body">
        {stageId !== 'info' ? (
          <div style={{ marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
            <AgentControlPanel status={status} errorMessage={errorMessage} compact />
          </div>
        ) : null}
        {children}
      </div>
    </aside>
  )
}
