import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ShellProvider } from './ShellContext'
import { TopBar } from './TopBar'
import { LeftRail } from './LeftRail'
import { StatusBar } from './StatusBar'

/**
 * Professional workspace shell: TopBar + LeftRail + main + StatusBar.
 */
export function MainLayout() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  return (
    <ShellProvider>
      <div className="workspace-shell app-shell">
        <TopBar
          onLogout={() => {
            logout()
            navigate('/login')
          }}
        />
        <div className="workspace-body">
          <LeftRail />
          <div className="main-pane">
            <Outlet />
          </div>
        </div>
        <StatusBar />
      </div>
    </ShellProvider>
  )
}
