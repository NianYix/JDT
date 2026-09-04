import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { StageDef } from '../workspace/stages'
import type { WorkflowStatus } from '../workspace/statusMap'

export type ShellJobSnapshot = {
  stage: StageDef | null
  status: WorkflowStatus | 'idle'
  errorMessage?: string | null
  requestRun: (() => void) | null
  hasRunning: boolean
}

const emptySnapshot: ShellJobSnapshot = {
  stage: null,
  status: 'idle',
  errorMessage: null,
  requestRun: null,
  hasRunning: false,
}

type ShellContextValue = {
  job: ShellJobSnapshot
  setJob: (job: ShellJobSnapshot) => void
  clearJob: () => void
}

const ShellContext = createContext<ShellContextValue | null>(null)

export function ShellProvider({ children }: { children: ReactNode }) {
  const [job, setJobState] = useState<ShellJobSnapshot>(emptySnapshot)

  const setJob = useCallback((next: ShellJobSnapshot) => {
    setJobState(next)
  }, [])

  const clearJob = useCallback(() => {
    setJobState(emptySnapshot)
  }, [])

  const value = useMemo(() => ({ job, setJob, clearJob }), [job, setJob, clearJob])

  return <ShellContext.Provider value={value}>{children}</ShellContext.Provider>
}

export function useShell() {
  const ctx = useContext(ShellContext)
  if (!ctx) throw new Error('useShell must be used within ShellProvider')
  return ctx
}
