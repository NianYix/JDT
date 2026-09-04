import { useEffect } from 'react'
import { Typography, message } from 'antd'
import type { Project } from '../api/projects'
import { useShell } from '../layouts/ShellContext'
import { PipelineCanvas } from './PipelineCanvas'
import { InspectorPanel } from './InspectorPanel'
import { WorkspaceProvider, useWorkspace } from './WorkspaceContext'
import { getStage } from './stages'
import { ProjectInfoTab } from '../pages/project-detail/ProjectInfoTab'
import { RequirementAnalysisTab } from '../pages/project-detail/RequirementAnalysisTab'
import { TechnicalPlanTab } from '../pages/project-detail/TechnicalPlanTab'
import { CodeGenerationTab } from '../pages/project-detail/CodeGenerationTab'
import { TestGenerationTab } from '../pages/project-detail/TestGenerationTab'
import { CodeReviewTab } from '../pages/project-detail/CodeReviewTab'
import { DebugSessionTab } from '../pages/project-detail/DebugSessionTab'
import { DevelopmentMetricsTab } from '../pages/project-detail/DevelopmentMetricsTab'

type Props = {
  project: Project
}

export function ProjectWorkspace({ project }: Props) {
  return (
    <WorkspaceProvider project={project}>
      <ProjectWorkspaceInner />
    </WorkspaceProvider>
  )
}

function ProjectWorkspaceInner() {
  const {
    project,
    setProject,
    selectedStageId,
    setSelectedStageId,
    stageStatuses,
    activeJob,
    requestRun,
    onJobSettled,
  } = useWorkspace()
  const { setJob, clearJob } = useShell()

  const hasRunning = Object.values(stageStatuses).some((s) => s === 'pending' || s === 'running')

  useEffect(() => {
    setJob({
      stage: getStage(selectedStageId),
      status: activeJob.status,
      errorMessage: activeJob.errorMessage,
      requestRun: () => {
        const stage = getStage(selectedStageId)
        if (!stage.runnable) {
          message.info('当前节点不可执行')
          return
        }
        requestRun()
      },
      hasRunning,
    })
    return () => clearJob()
  }, [
    selectedStageId,
    activeJob.status,
    activeJob.errorMessage,
    hasRunning,
    requestRun,
    setJob,
    clearJob,
  ])

  return (
    <div
      className="pipeline-workspace"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr minmax(360px, 420px)',
        height: '100%',
        minHeight: 0,
      }}
    >
      <div style={{ minWidth: 0, minHeight: 0, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        <div className="pipeline-workspace-toolbar">
          <div>
            <Typography.Text strong style={{ color: 'var(--text)', fontSize: 15 }}>
              {project.name}
            </Typography.Text>
            <div className="mono" style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
              LOGIC FLOW · PROJECT WORKSPACE
            </div>
          </div>
        </div>
        <PipelineCanvas
          selectedStageId={selectedStageId}
          stageStatuses={stageStatuses}
          onSelect={setSelectedStageId}
        />
      </div>

      <InspectorPanel
        stageId={selectedStageId}
        status={stageStatuses[selectedStageId] ?? 'idle'}
        errorMessage={activeJob.errorMessage}
      >
        <StageBody
          stageId={selectedStageId}
          project={project}
          setProject={setProject}
          onJobSettled={() => onJobSettled(selectedStageId)}
        />
      </InspectorPanel>
    </div>
  )
}

function StageBody({
  stageId,
  project,
  setProject,
  onJobSettled,
}: {
  stageId: string
  project: Project
  setProject: (p: Project) => void
  onJobSettled: () => void
}) {
  switch (stageId) {
    case 'info':
      return <ProjectInfoTab project={project} onProjectChange={setProject} />
    case 'requirement':
      return <RequirementAnalysisTab project={project} onJobSettled={onJobSettled} />
    case 'technical':
      return <TechnicalPlanTab project={project} onJobSettled={onJobSettled} />
    case 'coding':
      return <CodeGenerationTab project={project} onJobSettled={onJobSettled} />
    case 'testing':
      return <TestGenerationTab project={project} onJobSettled={onJobSettled} />
    case 'review':
      return <CodeReviewTab project={project} onJobSettled={onJobSettled} />
    case 'debugging':
      return <DebugSessionTab project={project} onJobSettled={onJobSettled} />
    case 'metrics':
      return <DevelopmentMetricsTab project={project} onJobSettled={onJobSettled} />
    default:
      return null
  }
}
