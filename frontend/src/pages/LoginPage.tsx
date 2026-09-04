import { Button, Card, Form, Input, Typography, message } from 'antd'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'

export function LoginPage() {
  const { login, token } = useAuth()
  const navigate = useNavigate()

  if (token) {
    return <Navigate to="/projects" replace />
  }

  return (
    <div className="auth-page">
      <Card title="登录" className="auth-card">
        <Form
          layout="vertical"
          onFinish={async (values: { email: string; password: string }) => {
            try {
              await login(values.email, values.password)
              message.success('登录成功')
              navigate('/projects')
            } catch (err) {
              message.error(err instanceof ApiError ? err.message : '登录失败')
            }
          }}
        >
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="you@example.com" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 8 }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
        <Typography.Paragraph style={{ marginTop: 16 }}>
          还没有账号？<Link to="/register">注册</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  )
}
