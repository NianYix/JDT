import { deriveTimelineSteps, type WorkflowStatus } from './statusMap'
import type { StageDef } from './stages'

type Props = {
  stage: StageDef | null
  status: WorkflowStatus | 'idle'
}

export function ExecutionTimeline({ stage, status }: Props) {
  const steps = deriveTimelineSteps(status)
  if (!stage) {
    return <span className="mono">EXEC ● IDLE</span>
  }

  const active = steps.find((s) => s.state === 'active' || s.state === 'failed')
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
      <span className="mono">
        {stage.nodeId} · {stage.title}
      </span>
      <span style={{ opacity: 0.5 }}>|</span>
      {steps.map((s, i) => (
        <span key={s.key} className="mono" style={{ opacity: s.state === 'todo' ? 0.45 : 1 }}>
          {String(i + 1).padStart(2, '0')} {glyph(s.state)}
        </span>
      ))}
      {active ? (
        <>
          <span style={{ opacity: 0.5 }}>|</span>
          <span>{active.label}</span>
        </>
      ) : null}
    </span>
  )
}

function glyph(state: string) {
  if (state === 'done') return '✓'
  if (state === 'active') return '▶'
  if (state === 'failed') return '✕'
  return '○'
}
