import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Select, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as cgApi from '../../api/codeGenerations'
import type { CodeGeneration } from '../../api/codeGenerations'
import * as tgApi from '../../api/testGenerations'
import type { TestGeneration } from '../../api/testGenerations'
import { ApiError } from '../../api/client'
import { RepoFilePicker } from '../../components/repo/RepoFilePicker'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, codeBlockStyle, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function TestGenerationTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [items, setItems] = useState<TestGeneration[]>([])
  const [selected, setSelected] = useState<TestGeneration | null>(null)
  const [codeGens, setCodeGens] = useState<CodeGeneration[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadList = useCallback(async () => {
    const page = await tgApi.listTestGenerations(project.id)
    setItems(page.items)
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
        const [tgPage, cgPage] = await Promise.all([
          tgApi.listTestGenerations(project.id),
          cgApi.listCodeGenerations(project.id),
        ])
        setItems(tgPage.items)
        setSelected(tgPage.items[0] ?? null)
        setCodeGens(cgPage.items.filter((g) => g.status === 'succeeded'))
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
      }
    })()
  }, [project.id])

  const result = selected?.result_json

  return (
    <div>
      <Typography.Paragraph type="secondary">
        描述待测目标，可选关联成功的 AI 编码记录或补充上下文。本阶段仅生成测试建议，不执行 pytest、不写入工作区。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: {
          code_generation_id?: string
          target_description: string
          context_text?: string
        }) => {
          const target = (values.target_description || '').trim()
          if (!target) {
            message.warning('请输入待测目标描述')
            return
          }

          setSubmitting(true)
          try {
            const payload: tgApi.TestGenerationCreatePayload = {
              target_description: target,
            }
            if (values.code_generation_id) {
              payload.code_generation_id = values.code_generation_id
            }
            const ctx = (values.context_text || '').trim()
            if (ctx) {
              payload.context_text = ctx
            }
            if (selectedFiles.length) {
              payload.selected_files = selectedFiles
            }

            const created = await tgApi.createTestGeneration(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => tgApi.getTestGeneration(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('测试建议生成完成')
            } else {
              message.warning(final.error_message || '生成失败')
            }
            form.resetFields(['context_text'])
            setSelectedFiles([])
            await loadList()
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
          name="target_description"
          label="待测目标"
          rules={[{ required: true, message: '请输入待测目标描述' }]}
        >
          <Input.TextArea
            rows={4}
            placeholder="例如：用户登录 API 的单元测试，覆盖成功与 401 场景…"
          />
        </Form.Item>
        <Form.Item name="code_generation_id" label="关联 AI 编码（可选）">
          <Select
            allowClear
            placeholder={codeGens.length ? '选择已成功的编码记录' : '暂无成功的编码记录'}
            options={codeGens.map((g) => ({
              value: g.id,
              label: g.result_json?.summary || g.task_description.slice(0, 48),
            }))}
            disabled={!codeGens.length}
          />
        </Form.Item>
        <Form.Item name="context_text" label="补充上下文（可选）">
          <Input.TextArea rows={4} placeholder="可粘贴被测代码片段、Mock 约束等…" />
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
          生成测试建议
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={items}
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
            render: (status: TestGeneration['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary ||
              row.error_message ||
              row.target_description.slice(0, 60),
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
                <strong>测试策略：</strong>
                {result.testing_strategy}
              </Typography.Paragraph>
              <ResultList title="Fixtures / Mocks" items={result.fixtures_and_mocks} />
              <ResultList title="覆盖说明" items={result.coverage_notes} />
              <ResultList title="风险" items={result.risks} />
              <ResultList title="待澄清问题" items={result.open_questions} />
              {result.test_cases?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>测试用例</Typography.Text>
                  <Table
                    rowKey="name"
                    size="small"
                    pagination={false}
                    style={{ marginTop: 8 }}
                    dataSource={result.test_cases}
                    columns={[
                      { title: '名称', dataIndex: 'name', width: 140 },
                      { title: '类型', dataIndex: 'type', width: 90 },
                      { title: '描述', dataIndex: 'description' },
                      {
                        title: '步骤',
                        dataIndex: 'steps',
                        render: (steps: string[]) => steps?.join(' → ') || '',
                      },
                      { title: '预期', dataIndex: 'expected', width: 160 },
                    ]}
                  />
                </div>
              )}
              {result.test_files?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <Typography.Text strong>建议测试文件</Typography.Text>
                  {result.test_files.map((file) => (
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
            待测目标：{selected.target_description}
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
