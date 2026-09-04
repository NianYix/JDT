import { Button, Typography } from 'antd'
import { Link } from 'react-router-dom'

const { Title, Paragraph } = Typography

/**
 * Foundation dashboard — links into project workspace.
 */
export function Dashboard() {
  return (
    <div className="main-pane-padded dashboard">
      <Title level={3} className="page-title">
        Dashboard
      </Title>
      <Paragraph type="secondary" style={{ maxWidth: 560, marginTop: 12 }}>
        AI Engineering Copilot 工作台。从项目进入 Logic Flow，编排需求分析到研发度量的工程流水线。
      </Paragraph>
      <Button type="primary">
        <Link to="/projects">进入项目</Link>
      </Button>
    </div>
  )
}
