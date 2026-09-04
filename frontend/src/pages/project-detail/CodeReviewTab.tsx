import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Select, Table, Tag, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as cgApi from '../../api/codeGenerations'
import type { CodeGeneration } from '../../api/codeGenerations'
import * as crApi from '../../api/codeReviews'
import type { CodeReview } from '../../api/codeReviews'
import { ApiError } from '../../api/client'
import { RepoFilePicker } from '../../components/repo/RepoFilePicker'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, codeBlockStyle, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function CodeReviewTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [reviews, setReviews] = useState<CodeReview[]>([])
  const [selected, setSelected] = useState<CodeReview | null>(null)
  const [codeGens, setCodeGens] = useState<CodeGeneration[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadList = useCallback(async () => {
    const page = await crApi.listCodeReviews(project.id)
    setReviews(page.items)
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
        const [reviewPage, cgPage] = await Promise.all([
          crApi.listCodeReviews(project.id),
          cgApi.listCodeGenerations(project.id),
        ])
        setReviews(reviewPage.items)
        setSelected(reviewPage.items[0] ?? null)
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
        描述审查范围，可选关联成功的 AI 编码记录或粘贴待审代码。本阶段仅生成审查报告，不会自动修改工作区。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: {
          code_generation_id?: string
          review_scope: string
          context_text?: string
        }) => {
          const scope = (values.review_scope || '').trim()
          if (!scope) {
            message.warning('请输入审查范围')
            return
          }

          setSubmitting(true)
          try {
            const payload: crApi.CodeReviewCreatePayload = { review_scope: scope }
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

            const created = await crApi.createCodeReview(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => crApi.getCodeReview(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('代码审查完成')
            } else {
              message.warning(final.error_message || '审查失败')
            }
            form.resetFields(['context_text'])
            setSelectedFiles([])
            await loadList()
            setSelected(final)
            onJobSettled?.()
          } catch (err) {
            message.error(err instanceof ApiError ? err.message : '审查请求失败')
          } finally {
            setSubmitting(false)
          }
        }}
      >
        <Form.Item
          name="review_scope"
          label="审查范围"
          rules={[{ required: true, message: '请输入审查范围' }]}
        >
          <Input.TextArea
            rows={3}
            placeholder="例如：审查登录 API 的安全性、错误处理与可维护性…"
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
        <Form.Item name="context_text" label="待审代码 / 补充说明（可选）">
          <Input.TextArea rows={6} placeholder="粘贴待审查的代码片段或 PR 说明…" />
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
          开始审查
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={reviews}
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
            render: (status: CodeReview['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary || row.error_message || row.review_scope.slice(0, 60),
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
          <Typography.Title level={5}>审查结果</Typography.Title>
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
                <strong>总体评价：</strong>
                {result.overall_assessment}
              </Typography.Paragraph>
              <ResultList title="优点" items={result.strengths} />
              <ResultList title="安全" items={result.security_notes} />
              <ResultList title="性能" items={result.performance_notes} />
              <ResultList title="可维护性" items={result.maintainability_notes} />
              <ResultList title="待澄清问题" items={result.open_questions} />
              {result.issues?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>问题列表</Typography.Text>
                  <Table
                    rowKey={(row) => `${row.location}-${row.description}`}
                    size="small"
                    pagination={false}
                    style={{ marginTop: 8 }}
                    dataSource={result.issues}
                    columns={[
                      {
                        title: '严重级别',
                        dataIndex: 'severity',
                        width: 100,
                        render: (v: string) => (
                          <Tag
                            color={
                              v === 'critical' ? 'red' : v === 'major' ? 'orange' : 'default'
                            }
                          >
                            {v}
                          </Tag>
                        ),
                      },
                      { title: '位置', dataIndex: 'location', width: 140 },
                      { title: '类别', dataIndex: 'category', width: 100 },
                      { title: '描述', dataIndex: 'description' },
                      { title: '建议', dataIndex: 'suggestion', width: 180 },
                    ]}
                  />
                </div>
              )}
              {result.suggested_fixes?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <Typography.Text strong>建议修改</Typography.Text>
                  {result.suggested_fixes.map((fix) => (
                    <div key={fix.path || fix.description} style={{ marginTop: 12 }}>
                      <Typography.Paragraph>
                        <strong>{fix.path || '未命名'}</strong>
                      </Typography.Paragraph>
                      {fix.description && (
                        <Typography.Paragraph type="secondary">
                          {fix.description}
                        </Typography.Paragraph>
                      )}
                      {fix.content && <pre style={codeBlockStyle}>{fix.content}</pre>}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            审查范围：{selected.review_scope}
          </Typography.Paragraph>
          {selected.context_text && (
            <Typography.Paragraph type="secondary">
              待审内容：{selected.context_text}
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
