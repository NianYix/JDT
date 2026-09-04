import { Button, Space, Tooltip, Typography, message } from 'antd'
import {
  MoonOutlined,
  SunOutlined,
  CaretRightOutlined,
  BorderOutlined,
  BugOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'
import { useShell } from './ShellContext'
import { StatusDot } from '../components/workflow/StatusDot'
import { toVisualStatus } from '../workspace/statusMap'

type Props = {
  onLogout: () => void
}

export function TopBar({ onLogout }: Props) {
  const { user } = useAuth()
  const { mode, toggle } = useTheme()
  const { job } = useShell()
  const location = useLocation()
  const inProject = location.pathname.startsWith('/projects/') && location.pathname !== '/projects'

  const visual = toVisualStatus(job.status)

  return (
    <header className="top-bar">
      <div className="top-bar-group">
        <div className="brand-mark">AEC</div>
        <Typography.Text strong style={{ color: 'var(--text)' }}>
          AI Engineering Copilot
        </Typography.Text>
        {inProject && job.stage ? (
          <>
            <div className="top-bar-divider" />
            <span className="mono" style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              {job.stage.nodeId} · {job.stage.title}
            </span>
          </>
        ) : null}
      </div>

      <div className="top-bar-group">
        {inProject ? (
          <>
            <Tooltip title={job.stage?.runnable ? '运行当前阶段' : '当前节点不可执行'}>
              <Button
                type="primary"
                size="small"
                icon={<CaretRightOutlined />}
                disabled={!job.stage?.runnable || !job.requestRun}
                onClick={() => job.requestRun?.()}
              >
                Run
              </Button>
            </Tooltip>
            <Tooltip title="后端暂不支持取消进行中的任务">
              <Button
                size="small"
                icon={<BorderOutlined />}
                disabled={!job.hasRunning}
                onClick={() => message.info('后端暂不支持取消进行中的 LLM 任务')}
              >
                Stop
              </Button>
            </Tooltip>
            <Tooltip title="AI Agent">
              <Button size="small" icon={<ThunderboltOutlined />} disabled>
                AI
              </Button>
            </Tooltip>
            <Tooltip title="Debug">
              <Button size="small" icon={<BugOutlined />} disabled>
                Debug
              </Button>
            </Tooltip>
            <div className="top-bar-divider" />
          </>
        ) : null}

        <Space size={10} align="center">
          <StatusDot visual={visual === 'idle' ? 'completed' : visual} />
          <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Connected
          </span>
        </Space>

        <Tooltip title={mode === 'dark' ? '切换浅色' : '切换深色'}>
          <Button
            size="small"
            type="text"
            icon={mode === 'dark' ? <SunOutlined /> : <MoonOutlined />}
            onClick={toggle}
            aria-label="切换主题"
          />
        </Tooltip>

        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {user?.display_name}
        </Typography.Text>
        <Button size="small" onClick={onLogout}>
          退出
        </Button>
      </div>
    </header>
  )
}
