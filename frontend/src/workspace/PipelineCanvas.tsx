import { useLayoutEffect, useRef, useState } from 'react'
import { PipelineNode } from './PipelineNode'
import { STAGES, type StageId } from './stages'
import { toVisualStatus, type WorkflowStatus } from './statusMap'

type Props = {
  selectedStageId: StageId
  stageStatuses: Record<StageId, WorkflowStatus | 'idle'>
  onSelect: (id: StageId) => void
}

type EdgeGeom = {
  from: StageId
  to: StageId
  d: string
  state: 'default' | 'active' | 'running' | 'error'
}

export function PipelineCanvas({ selectedStageId, stageStatuses, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const nodeEls = useRef<Partial<Record<StageId, HTMLDivElement | null>>>({})
  const [edges, setEdges] = useState<EdgeGeom[]>([])

  useLayoutEffect(() => {
    const container = containerRef.current
    if (!container) return

    const measure = () => {
      const cRect = container.getBoundingClientRect()
      const next: EdgeGeom[] = []
      for (let i = 0; i < STAGES.length - 1; i++) {
        const from = STAGES[i]
        const to = STAGES[i + 1]
        const a = nodeEls.current[from.id]
        const b = nodeEls.current[to.id]
        if (!a || !b) continue
        const ar = a.getBoundingClientRect()
        const br = b.getBoundingClientRect()
        const x1 = ar.right - cRect.left
        const y1 = ar.top + ar.height / 2 - cRect.top
        const x2 = br.left - cRect.left
        const y2 = br.top + br.height / 2 - cRect.top
        const dx = Math.max(40, (x2 - x1) / 2)
        const d = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`

        const fromV = toVisualStatus(stageStatuses[from.id])
        const toV = toVisualStatus(stageStatuses[to.id])
        let state: EdgeGeom['state'] = 'default'
        if (fromV === 'error' || toV === 'error') state = 'error'
        else if (fromV === 'running' || toV === 'running') state = 'running'
        else if (from.id === selectedStageId || to.id === selectedStageId) state = 'active'

        next.push({ from: from.id, to: to.id, d, state })
      }
      setEdges(next)
    }

    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(container)
    window.addEventListener('resize', measure)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', measure)
    }
  }, [selectedStageId, stageStatuses])

  return (
    <div className="pipeline-canvas" ref={containerRef}>
      <svg className="pipeline-svg" aria-hidden>
        {edges.map((e) => (
          <path
            key={`${e.from}-${e.to}`}
            d={e.d}
            className={`pipeline-edge ${e.state}`}
          />
        ))}
      </svg>
      <div className="pipeline-row">
        {STAGES.map((stage) => (
          <PipelineNode
            key={stage.id}
            stage={stage}
            selected={selectedStageId === stage.id}
            status={stageStatuses[stage.id] ?? 'idle'}
            nodeRef={(el) => {
              nodeEls.current[stage.id] = el
            }}
            onSelect={() => onSelect(stage.id)}
          />
        ))}
      </div>
    </div>
  )
}
