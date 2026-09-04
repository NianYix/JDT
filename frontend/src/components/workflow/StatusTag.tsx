import { Tag } from 'antd'
import { StatusDot } from './StatusDot'
import { toVisualStatus, visualLabel, type WorkflowStatus } from '../../workspace/statusMap'

export type { WorkflowStatus }

const TAG_COLOR: Record<string, string> = {
  idle: 'default',
  pending: 'default',
  running: 'processing',
  succeeded: 'success',
  failed: 'error',
}

export function StatusTag({ status }: { status: WorkflowStatus }) {
  const visual = toVisualStatus(status)
  return (
    <Tag color={TAG_COLOR[status] ?? 'default'} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <StatusDot visual={visual} />
      <span className="mono">{visualLabel(visual)}</span>
    </Tag>
  )
}
