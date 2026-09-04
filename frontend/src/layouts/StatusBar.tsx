import { useShell } from './ShellContext'
import { ExecutionTimeline } from '../workspace/ExecutionTimeline'
import { StatusDot } from '../components/workflow/StatusDot'
import { toVisualStatus, visualLabel } from '../workspace/statusMap'

export function StatusBar() {
  const { job } = useShell()
  const visual = toVisualStatus(job.status)

  return (
    <footer className="status-bar">
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <StatusDot visual={visual} />
        <span className="mono">{visualLabel(visual)}</span>
      </span>
      <span style={{ opacity: 0.35 }}>|</span>
      <ExecutionTimeline stage={job.stage} status={job.status} />
    </footer>
  )
}
