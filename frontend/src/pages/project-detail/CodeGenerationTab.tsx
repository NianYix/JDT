import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Select, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as tpApi from '../../api/technicalPlans'
import type { TechnicalPlan } from '../../api/technicalPlans'
import * as cgApi from '../../api/codeGenerations'
import type { CodeGeneration } from '../../api/codeGenerations'
import { ApiError } from '../../api/client'
import { RepoFilePicker } from '../../components/repo/RepoFilePicker'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, codeBlockStyle, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function CodeGenerationTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [generations, setGenerations] = useState<CodeGeneration[]>([])
  const [selected, setSelected] = useState<CodeGeneration | null>(null)
  const [plans, setPlans] = useState<TechnicalPlan[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadGenerations = useCallback(async () => {
    const page = await cgApi.listCodeGenerations(project.id)
    setGenerations(page.items)
    setSelected((prev) => {
      if (prev) {
        const fresh = page.items.find((item) => item.id === prev.id)
        if (fresh) return fresh
      }
      return page.items[0] ?? null
    })
  }, [project.id])

  useEffect(() => {
    ;(async () => {
      try {
        const [genPage, planPage] = await Promise.all([
          cgApi.listCodeGenerations(project.id),
          tpApi.listTechnicalPlans(project.id),
        ])
        setGenerations(genPage.items)
        setSelected(genPage.items[0] ?? null)
        setPlans(planPage.items.filter((p) => p.status === 'succeeded'))
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
      }
    })()
  }, [project.id])

  const result = selected?.result_json

  return (
    <div>
      <Typography.Paragraph type="secondary">
        描述编码任务，可选关联成功的技术规划或补充上下文。本阶段仅生成可审阅的代码建议，不会写入工作区。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: {
          technical_plan_id?: string
          task_description: string
          context_text?: string
        }) => {
          const task = (values.task_description || '').trim()
          if (!task) {
            message.warning('请输入编码任务描述')
            return
          }

          setSubmitting(true)
          try {
            const payload: cgApi.CodeGenerationCreatePayload = {
              task_description: task,
            }
            if (values.technical_plan_id) {
              payload.technical_plan_id = values.technical_plan_id
            }
            const ctx = (values.context_text || '').trim()
            if (ctx) {
              payload.context_text = ctx
            }
            if (selectedFiles.length) {
              payload.selected_files = selectedFiles
            }

            const created = await cgApi.createCodeGeneration(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => cgApi.getCodeGeneration(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('代码建议生成完成')
            } else {
              message.warning(final.error_message || '生成失败')
            }
            form.resetFields(['context_text'])
            setSelectedFiles([])
            await loadGenerations()
            setSelected(final)
            onJobSettled?.()
          } catch (err) {
            message.error(err instanceof ApiError ? err.message : '生成请求失败')
          } finally {
            setSubmitting(false)
          }
        }}
      >
        <Form.Item
          name="task_description"
          label="编码任务"
          rules={[{ required: true, message: '请输入编码任务描述' }]}
        >
          <Input.TextArea
            rows={4}
            placeholder="例如：实现用户登录 API，返回 JWT access token…"
          />
        </Form.Item>
        <Form.Item name="technical_plan_id" label="关联技术规划（可选）">
          <Select
            allowClear
            placeholder={plans.length ? '选择已成功的技术规划' : '暂无成功的技术规划'}
            options={plans.map((p) => ({
              value: p.id,
              label: p.result_json?.summary || p.context_text?.slice(0, 48) || '技术规划',
            }))}
            disabled={!plans.length}
          />
        </Form.Item>
        <Form.Item name="context_text" label="补充上下文（可选）">
          <Input.TextArea rows={4} placeholder="可粘贴现有代码片段、技术约束等…" />
        </Form.Item>
        <Form.Item label="仓库文件（可选）">
          <RepoFilePicker
            projectId={project.id}
            value={selectedFiles}
            onChange={setSelectedFiles}
            disabled={submitting}
          />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={submitting}>
          生成代码建议
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={generations}
        pagination={false}
        onRow={(record) => ({
          onClick: () => setSelected(record),
          style: { cursor: 'pointer' },
        })}
        columns={[
          {
            title: '状态',
            dataIndex: 'status',
            width: 110,
            render: (status: CodeGeneration['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary ||
              row.error_message ||
              row.task_description.slice(0, 60),
          },
          {
            title: '时间',
            dataIndex: 'created_at',
            width: 200,
            render: (v: string) => new Date(v).toLocaleString(),
          },
        ]}
      />

      {selected && (
        <div style={{ marginTop: 24, maxWidth: 900 }}>
          <Typography.Title level={5}>生成结果</Typography.Title>
          <Typography.Paragraph>
            <StatusTag status={selected.status} />
            {selected.model_name && (
              <Typography.Text type="secondary"> model: {selected.model_name}</Typography.Text>
            )}
          </Typography.Paragraph>
          {selected.status === 'failed' && (
            <Typography.Paragraph type="danger">{selected.error_message}</Typography.Paragraph>
          )}
          {result && (
            <>
              <Typography.Paragraph>
                <strong>摘要：</strong>
                {result.summary}
              </Typography.Paragraph>
              <Typography.Paragraph>
                <strong>实现思路：</strong>
                {result.approach}
              </Typography.Paragraph>
              <ResultList title="实现步骤" items={result.implementation_steps} />
              <ResultList title="依赖" items={result.dependencies} />
              <ResultList title="测试建议" items={result.testing_notes} />
              <ResultList title="风险" items={result.risks} />
              <ResultList title="待澄清问题" items={result.open_questions} />
              {result.files?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <Typography.Text strong>建议文件</Typography.Text>
                  {result.files.map((file) => (
                    <div key={file.path || file.description} style={{ marginTop: 12 }}>
                      <Typography.Paragraph>
                        <strong>{file.path || '未命名'}</strong>
                        {file.language && (
                          <Typography.Text type="secondary"> ({file.language})</Typography.Text>
                        )}
                      </Typography.Paragraph>
                      {file.description && (
                        <Typography.Paragraph type="secondary">
                          {file.description}
                        </Typography.Paragraph>
                      )}
                      {file.content && <pre style={codeBlockStyle}>{file.content}</pre>}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            任务：{selected.task_description}
          </Typography.Paragraph>
          {selected.context_text && (
            <Typography.Paragraph type="secondary">
              补充上下文：{selected.context_text}
            </Typography.Paragraph>
          )}
          {selected.selected_files && selected.selected_files.length > 0 && (
            <Typography.Paragraph type="secondary">
              附带文件：{selected.selected_files.join(', ')}
            </Typography.Paragraph>
          )}
        </div>
      )}
    </div>
  )
}
