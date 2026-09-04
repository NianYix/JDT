import { DashboardOutlined, ProjectOutlined } from '@ant-design/icons'
import { Tooltip } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'

export function LeftRail() {
  const navigate = useNavigate()
  const location = useLocation()

  const selected = location.pathname.startsWith('/projects') ? 'projects' : 'dashboard'

  return (
    <aside className="left-rail">
      <Tooltip title="Dashboard" placement="right">
        <button
          type="button"
          className={`left-rail-btn${selected === 'dashboard' ? ' active' : ''}`}
          onClick={() => navigate('/')}
        >
          <DashboardOutlined />
        </button>
      </Tooltip>
      <Tooltip title="项目" placement="right">
        <button
          type="button"
          className={`left-rail-btn${selected === 'projects' ? ' active' : ''}`}
          onClick={() => navigate('/projects')}
        >
          <ProjectOutlined />
        </button>
      </Tooltip>
    </aside>
  )
}
