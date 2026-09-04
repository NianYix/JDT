import { nodeKindColors } from '../theme/tokens'
import { StatusDot } from '../components/workflow/StatusDot'
import { toVisualStatus, visualLabel, type WorkflowStatus } from './statusMap'
import type { StageDef } from './stages'

type Props = {
  stage: StageDef
  selected: boolean
  status: WorkflowStatus | 'idle'
  nodeRef?: (el: HTMLDivElement | null) => void
  onSelect: () => void
}

export function PipelineNode({ stage, selected, status, nodeRef, onSelect }: Props) {
  const visual = toVisualStatus(status)
  const kindColor = nodeKindColors[stage.kind]

  return (
    <div
      ref={nodeRef}
      className={`pipeline-node${selected ? ' selected' : ''}${visual === 'running' ? ' running' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      <div className="pipeline-node-header">
        <span className="pipeline-node-kind" style={{ background: kindColor }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="pipeline-node-title">{stage.title}</div>
          <div className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
            {stage.nodeId}
          </div>
        </div>
        <StatusDot visual={visual} title={visualLabel(visual)} />
      </div>
      <div className="pipeline-node-body">
        <div>{stage.description}</div>
        <div>
          Status{' '}
          <span className="mono" style={{ color: 'var(--text)' }}>
            ● {visualLabel(visual)}
          </span>
        </div>
      </div>
    </div>
  )
}
