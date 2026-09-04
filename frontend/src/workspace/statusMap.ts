export type WorkflowStatus = 'pending' | 'running' | 'succeeded' | 'failed' | string

export type VisualStatus = 'idle' | 'running' | 'completed' | 'error' | 'warning'

export function toVisualStatus(status: WorkflowStatus | 'idle' | undefined | null): VisualStatus {
  if (!status || status === 'idle') return 'idle'
  if (status === 'pending' || status === 'running') return 'running'
  if (status === 'succeeded') return 'completed'
  if (status === 'failed') return 'error'
  return 'idle'
}

export function visualLabel(visual: VisualStatus): string {
  switch (visual) {
    case 'idle':
      return 'IDLE'
    case 'running':
      return 'RUNNING'
    case 'completed':
      return 'COMPLETED'
    case 'error':
      return 'ERROR'
    case 'warning':
      return 'WARNING'
  }
}

export type TimelineStepState = 'done' | 'active' | 'todo' | 'failed'

export function deriveTimelineSteps(status: WorkflowStatus | 'idle' | undefined | null): {
  key: string
  label: string
  state: TimelineStepState
}[] {
  const steps = [
    { key: 'queue', label: 'Queue / Accept' },
    { key: 'invoke', label: 'Invoke Model' },
    { key: 'persist', label: 'Persist Result' },
  ]

  if (!status || status === 'idle') {
    return steps.map((s) => ({ ...s, state: 'todo' as const }))
  }
  if (status === 'pending') {
    return [
      { ...steps[0], state: 'active' },
      { ...steps[1], state: 'todo' },
      { ...steps[2], state: 'todo' },
    ]
  }
  if (status === 'running') {
    return [
      { ...steps[0], state: 'done' },
      { ...steps[1], state: 'active' },
      { ...steps[2], state: 'todo' },
    ]
  }
  if (status === 'succeeded') {
    return steps.map((s) => ({ ...s, state: 'done' as const }))
  }
  if (status === 'failed') {
    return [
      { ...steps[0], state: 'done' },
      { ...steps[1], state: 'failed' },
      { ...steps[2], state: 'todo' },
    ]
  }
  return steps.map((s) => ({ ...s, state: 'todo' as const }))
}
