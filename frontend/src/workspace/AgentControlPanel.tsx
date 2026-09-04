import { StatusDot } from '../components/workflow/StatusDot'
import { deriveTimelineSteps, toVisualStatus, visualLabel, type WorkflowStatus } from './statusMap'

type Props = {
  status: WorkflowStatus | 'idle'
  errorMessage?: string | null
  compact?: boolean
}

export function AgentControlPanel({ status, errorMessage, compact }: Props) {
  const visual = toVisualStatus(status)
  const steps = deriveTimelineSteps(status)

  return (
    <div className="agent-panel" style={compact ? { borderTop: 'none', padding: 0, marginTop: 0 } : undefined}>
      <div className="agent-panel-title">AGENT</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <StatusDot visual={visual} />
        <span className="mono" style={{ color: 'var(--text)' }}>
          {visualLabel(visual)}
        </span>
      </div>
      {steps.map((step) => (
        <div key={step.key} className="timeline-step">
          <span className="mono" style={{ width: 12, color: stepStateColor(step.state) }}>
            {stepStateGlyph(step.state)}
          </span>
          <div>
            <div style={{ color: 'var(--text)' }}>{step.label}</div>
          </div>
        </div>
      ))}
      {errorMessage ? (
        <div style={{ marginTop: 8, color: 'var(--error)', wordBreak: 'break-word' }}>{errorMessage}</div>
      ) : null}
    </div>
  )
}

function stepStateGlyph(state: string) {
  if (state === 'done') return '✓'
  if (state === 'active') return '▶'
  if (state === 'failed') return '✕'
  return '○'
}

function stepStateColor(state: string) {
  if (state === 'done') return 'var(--success)'
  if (state === 'active') return 'var(--accent-primary)'
  if (state === 'failed') return 'var(--error)'
  return 'var(--text-secondary)'
}
