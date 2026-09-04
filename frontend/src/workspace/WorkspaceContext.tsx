import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { Project } from '../api/projects'
import * as raApi from '../api/requirementAnalyses'
import * as tpApi from '../api/technicalPlans'
import * as cgApi from '../api/codeGenerations'
import * as tgApi from '../api/testGenerations'
import * as crApi from '../api/codeReviews'
import * as dsApi from '../api/debugSessions'
import * as dmApi from '../api/developmentMetrics'
import { getStage, type StageId } from './stages'
import type { WorkflowStatus } from './statusMap'

type StageStatusMap = Record<StageId, WorkflowStatus | 'idle'>

type ActiveJob = {
  stageId: StageId
  status: WorkflowStatus | 'idle'
  errorMessage?: string | null
}

type WorkspaceContextValue = {
  project: Project
  setProject: (p: Project) => void
  selectedStageId: StageId
  setSelectedStageId: (id: StageId) => void
  stageStatuses: StageStatusMap
  activeJob: ActiveJob
  refreshStageStatus: (id: StageId) => Promise<void>
  refreshAllStatuses: () => Promise<void>
  requestRun: () => void
  registerRunHandler: (handler: (() => void) | null) => void
  onJobSettled: (stageId: StageId) => void
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

const AI_STAGES: StageId[] = [
  'requirement',
  'technical',
  'coding',
  'testing',
  'review',
  'debugging',
  'metrics',
]

function emptyStatuses(): StageStatusMap {
  return {
    info: 'idle',
    requirement: 'idle',
    technical: 'idle',
    coding: 'idle',
    testing: 'idle',
    review: 'idle',
    debugging: 'idle',
    metrics: 'idle',
  }
}

async function fetchLatestStatus(projectId: string, stageId: StageId): Promise<WorkflowStatus | 'idle'> {
  try {
    switch (stageId) {
      case 'requirement': {
        const page = await raApi.listRequirementAnalyses(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'technical': {
        const page = await tpApi.listTechnicalPlans(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'coding': {
        const page = await cgApi.listCodeGenerations(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'testing': {
        const page = await tgApi.listTestGenerations(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'review': {
        const page = await crApi.listCodeReviews(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'debugging': {
        const page = await dsApi.listDebugSessions(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      case 'metrics': {
        const page = await dmApi.listDevelopmentMetrics(projectId, 1, 1)
        return page.items[0]?.status ?? 'idle'
      }
      default:
        return 'idle'
    }
  } catch {
    return 'idle'
  }
}

async function fetchLatestError(projectId: string, stageId: StageId): Promise<string | null> {
  try {
    switch (stageId) {
      case 'requirement':
        return (await raApi.listRequirementAnalyses(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'technical':
        return (await tpApi.listTechnicalPlans(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'coding':
        return (await cgApi.listCodeGenerations(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'testing':
        return (await tgApi.listTestGenerations(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'review':
        return (await crApi.listCodeReviews(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'debugging':
        return (await dsApi.listDebugSessions(projectId, 1, 1)).items[0]?.error_message ?? null
      case 'metrics':
        return (await dmApi.listDevelopmentMetrics(projectId, 1, 1)).items[0]?.error_message ?? null
      default:
        return null
    }
  } catch {
    return null
  }
}

export function WorkspaceProvider({
  project: initialProject,
  children,
}: {
  project: Project
  children: ReactNode
}) {
  const [project, setProject] = useState(initialProject)
  const [selectedStageId, setSelectedStageId] = useState<StageId>('requirement')
  const [stageStatuses, setStageStatuses] = useState<StageStatusMap>(emptyStatuses)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const runHandlerRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    setProject(initialProject)
  }, [initialProject])

  const refreshStageStatus = useCallback(async (id: StageId) => {
    if (id === 'info') return
    const status = await fetchLatestStatus(project.id, id)
    setStageStatuses((prev) => ({ ...prev, [id]: status }))
    if (id === selectedStageId) {
      const err = await fetchLatestError(project.id, id)
      setErrorMessage(err)
    }
  }, [project.id, selectedStageId])

  const refreshAllStatuses = useCallback(async () => {
    const entries = await Promise.all(
      AI_STAGES.map(async (id) => [id, await fetchLatestStatus(project.id, id)] as const),
    )
    setStageStatuses((prev) => {
      const next = { ...prev }
      for (const [id, status] of entries) next[id] = status
      return next
    })
  }, [project.id])

  useEffect(() => {
    void refreshAllStatuses()
  }, [refreshAllStatuses])

  useEffect(() => {
    void refreshStageStatus(selectedStageId)
  }, [selectedStageId, refreshStageStatus])

  // Poll while any stage is non-terminal
  useEffect(() => {
    const busy = AI_STAGES.some((id) => {
      const s = stageStatuses[id]
      return s === 'pending' || s === 'running'
    })
    if (!busy) return
    const timer = window.setInterval(() => {
      void refreshAllStatuses()
    }, 2000)
    return () => window.clearInterval(timer)
  }, [stageStatuses, refreshAllStatuses])

  const registerRunHandler = useCallback((handler: (() => void) | null) => {
    runHandlerRef.current = handler
  }, [])

  const requestRun = useCallback(() => {
    const stage = getStage(selectedStageId)
    if (!stage.runnable) return
    runHandlerRef.current?.()
  }, [selectedStageId])

  const onJobSettled = useCallback(
    (stageId: StageId) => {
      void refreshStageStatus(stageId)
      void refreshAllStatuses()
    },
    [refreshStageStatus, refreshAllStatuses],
  )

  const activeJob: ActiveJob = useMemo(
    () => ({
      stageId: selectedStageId,
      status: stageStatuses[selectedStageId] ?? 'idle',
      errorMessage,
    }),
    [selectedStageId, stageStatuses, errorMessage],
  )

  const value = useMemo(
    () => ({
      project,
      setProject,
      selectedStageId,
      setSelectedStageId,
      stageStatuses,
      activeJob,
      refreshStageStatus,
      refreshAllStatuses,
      requestRun,
      registerRunHandler,
      onJobSettled,
    }),
    [
      project,
      selectedStageId,
      stageStatuses,
      activeJob,
      refreshStageStatus,
      refreshAllStatuses,
      requestRun,
      registerRunHandler,
      onJobSettled,
    ],
  )

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace must be used within WorkspaceProvider')
  return ctx
}

/** Optional access when outside project workspace (e.g. TopBar on list page). */
export function useWorkspaceOptional() {
  return useContext(WorkspaceContext)
}
