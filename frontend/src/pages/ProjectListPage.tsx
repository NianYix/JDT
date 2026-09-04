import { useEffect, useState } from 'react'
import { Button, Form, Input, Modal, Space, Table, Typography, message } from 'antd'
import { Link } from 'react-router-dom'
import * as projectsApi from '../api/projects'
import type { Project } from '../api/projects'
import { ApiError } from '../api/client'

export function ProjectListPage() {
  const [items, setItems] = useState<Project[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const page = await projectsApi.listProjects()
      setItems(page.items)
      setTotal(page.total)
    } catch (err) {
      message.error(err instanceof ApiError ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="main-pane-padded">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} className="page-title">
          项目列表
        </Typography.Title>
        <Button type="primary" onClick={() => setOpen(true)}>
          新建项目
        </Button>
      </Space>
      <Typography.Paragraph type="secondary">共 {total} 个项目</Typography.Paragraph>
      <Table
        rowKey="id"
        loading={loading}
        dataSource={items}
        columns={[
          {
            title: '名称',
            dataIndex: 'name',
            render: (name: string, row) => <Link to={`/projects/${row.id}`}>{name}</Link>,
          },
          { title: '工作区路径', dataIndex: 'repo_path' },
          { title: '描述', dataIndex: 'description' },
        ]}
        pagination={false}
      />

      <Modal
        title="新建项目"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await projectsApi.createProject(values)
              message.success('已创建')
              setOpen(false)
              form.resetFields()
              await load()
            } catch (err) {
              message.error(err instanceof ApiError ? err.message : '创建失败')
            }
          }}
        >
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="repo_path" label="工作区路径">
            <Input placeholder="例如 D:/repos/my-app" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
