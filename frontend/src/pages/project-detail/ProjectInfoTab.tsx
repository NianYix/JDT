import { Button, Form, Input, Popconfirm, Space, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import * as projectsApi from '../../api/projects'
import type { Project } from '../../api/projects'
import { ApiError } from '../../api/client'

type Props = {
  project: Project
  onProjectChange: (project: Project) => void
}

export function ProjectInfoTab({ project, onProjectChange }: Props) {
  const navigate = useNavigate()
  const [form] = Form.useForm()

  return (
    <Form
      form={form}
      layout="vertical"
      style={{ maxWidth: '100%' }}
      initialValues={{
        name: project.name,
        description: project.description ?? '',
        repo_path: project.repo_path ?? '',
      }}
      onFinish={async (values) => {
        try {
          const updated = await projectsApi.updateProject(project.id, {
            name: values.name,
            description: values.description || null,
            repo_path: values.repo_path || null,
          })
          onProjectChange(updated)
          message.success('已保存')
        } catch (err) {
          message.error(err instanceof ApiError ? err.message : '保存失败')
        }
      }}
    >
      <Form.Item name="name" label="名称" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="repo_path" label="工作区路径">
        <Input />
      </Form.Item>
      <Form.Item name="description" label="描述">
        <Input.TextArea rows={4} />
      </Form.Item>
      <Space>
        <Button type="primary" htmlType="submit">
          保存
        </Button>
        <Popconfirm
          title="确认删除该项目？"
          onConfirm={async () => {
            try {
              await projectsApi.deleteProject(project.id)
              message.success('已删除')
              navigate('/projects')
            } catch (err) {
              message.error(err instanceof ApiError ? err.message : '删除失败')
            }
          }}
        >
          <Button danger>删除</Button>
        </Popconfirm>
      </Space>
    </Form>
  )
}
