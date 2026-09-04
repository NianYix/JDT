import type { NodeKind } from '../theme/tokens'

export type StageId =
  | 'info'
  | 'requirement'
  | 'technical'
  | 'coding'
  | 'testing'
  | 'review'
  | 'debugging'
  | 'metrics'

export type StageDef = {
  id: StageId
  nodeId: string
  title: string
  kind: NodeKind
  runnable: boolean
  description: string
}

export const STAGES: StageDef[] = [
  {
    id: 'info',
    nodeId: 'N-001',
    title: '项目信息',
    kind: 'system',
    runnable: false,
    description: 'System · Project config',
  },
  {
    id: 'requirement',
    nodeId: 'N-002',
    title: '需求分析',
    kind: 'logic',
    runnable: true,
    description: 'Logic · Requirement analysis',
  },
  {
    id: 'technical',
    nodeId: 'N-003',
    title: '技术规划',
    kind: 'logic',
    runnable: true,
    description: 'Logic · Technical plan',
  },
  {
    id: 'coding',
    nodeId: 'N-004',
    title: 'AI 编码',
    kind: 'action',
    runnable: true,
    description: 'Action · Code generation',
  },
  {
    id: 'testing',
    nodeId: 'N-005',
    title: '自动化测试',
    kind: 'action',
    runnable: true,
    description: 'Action · Test generation',
  },
  {
    id: 'review',
    nodeId: 'N-006',
    title: '代码审查',
    kind: 'ai',
    runnable: true,
    description: 'AI · Code review',
  },
  {
    id: 'debugging',
    nodeId: 'N-007',
    title: 'AI 调试',
    kind: 'ai',
    runnable: true,
    description: 'AI · Debug session',
  },
  {
    id: 'metrics',
    nodeId: 'N-008',
    title: '研发度量',
    kind: 'data',
    runnable: true,
    description: 'Data · Dev metrics',
  },
]

export function getStage(id: StageId): StageDef {
  return STAGES.find((s) => s.id === id) ?? STAGES[0]
}
