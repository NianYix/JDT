import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Select, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as cgApi from '../../api/codeGenerations'
import type { CodeGeneration } from '../../api/codeGenerations'
import * as crApi from '../../api/codeReviews'
import type { CodeReview } from '../../api/codeReviews'
import * as dbApi from '../../api/debugSessions'
import type { DebugSession } from '../../api/debugSessions'
import { ApiError } from '../../api/client'
import { RepoFilePicker } from '../../components/repo/RepoFilePicker'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, codeBlockStyle, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function DebugSessionTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [sessions, setSessions] = useState<DebugSession[]>([])
  const [selected, setSelected] = useState<DebugSession | null>(null)
  const [codeReviews, setCodeReviews] = useState<CodeReview[]>([])
  const [codeGens, setCodeGens] = useState<CodeGeneration[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadList = useCallback(async () => {
    const page = await dbApi.listDebugSessions(project.id)
    setSessions(page.items)
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
        const [sessionPage, reviewPage, cgPage] = await Promise.all([
          dbApi.listDebugSessions(project.id),
          crApi.listCodeReviews(project.id),
          cgApi.listCodeGenerations(project.id),
        ])
        setSessions(sessionPage.items)
        setSelected(sessionPage.items[0] ?? null)
        setCodeReviews(reviewPage.items.filter((r) => r.status === 'succeeded'))
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
        描述问题现象（错误、堆栈、复现步骤），可选关联审查/编码记录或粘贴日志。本阶段仅生成排查建议，不自动修复。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: {
          code_review_id?: string
          code_generation_id?: string
          problem_description: string
          context_text?: string
        }) => {
          const problem = (values.problem_description || '').trim()
          if (!problem) {
            message.warning('请输入问题描述')
            return
          }

          setSubmitting(true)
          try {
            const payload: dbApi.DebugSessionCreatePayload = {
              problem_description: problem,
            }
            if (values.code_review_id) {
              payload.code_review_id = values.code_review_id
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

            const created = await dbApi.createDebugSession(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => dbApi.getDebugSession(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('调试分析完成')
            } else {
              message.warning(final.error_message || '分析失败')
            }
            form.resetFields(['context_text'])
            setSelectedFiles([])
            await loadList()
            setSelected(final)
            onJobSettled?.()
          } catch (err) {
            message.error(err instanceof ApiError ? err.message : '分析请求失败')
          } finally {
            setSubmitting(false)
          }
        }}
      >
        <Form.Item
          name="problem_description"
          label="问题描述"
          rules={[{ required: true, message: '请输入问题描述' }]}
        >
          <Input.TextArea
            rows={4}
            placeholder="例如：登录接口间歇性 500，堆栈显示 KeyError…"
          />
        </Form.Item>
        <Form.Item name="code_review_id" label="关联代码审查（可选）">
          <Select
            allowClear
            placeholder={
              codeReviews.length ? '选择已成功的审查记录' : '暂无成功的审查记录'
            }
            options={codeReviews.map((r) => ({
              value: r.id,
              label: r.result_json?.summary || r.review_scope.slice(0, 48),
            }))}
            disabled={!codeReviews.length}
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
        <Form.Item name="context_text" label="日志 / 堆栈（可选）">
          <Input.TextArea rows={6} placeholder="粘贴错误堆栈、日志片段…" />
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
          开始调试分析
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={sessions}
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
            render: (status: DebugSession['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary ||
              row.error_message ||
              row.problem_description.slice(0, 60),
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
          <Typography.Title level={5}>分析结果</Typography.Title>
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
                <strong>根因分析：</strong>
                {result.root_cause_analysis}
              </Typography.Paragraph>
              <ResultList title="排查步骤" items={result.debugging_steps} />
              <ResultList title="验证步骤" items={result.verification_steps} />
              <ResultList title="预防建议" items={result.prevention_notes} />
              <ResultList title="待澄清问题" items={result.open_questions} />
              {result.likely_causes?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>可能原因</Typography.Text>
                  <Table
                    rowKey={(row) => row.hypothesis}
                    size="small"
                    pagination={false}
                    style={{ marginTop: 8 }}
                    dataSource={result.likely_causes}
                    columns={[
                      { title: '假设', dataIndex: 'hypothesis' },
                      { title: '置信度', dataIndex: 'confidence', width: 100 },
                      { title: '依据', dataIndex: 'evidence' },
                    ]}
                  />
                </div>
              )}
              {result.fix_suggestions?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <Typography.Text strong>修复建议</Typography.Text>
                  {result.fix_suggestions.map((fix) => (
                    <div key={fix.description || fix.content} style={{ marginTop: 12 }}>
                      {fix.description && (
                        <Typography.Paragraph>{fix.description}</Typography.Paragraph>
                      )}
                      {fix.content && <pre style={codeBlockStyle}>{fix.content}</pre>}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            问题：{selected.problem_description}
          </Typography.Paragraph>
          {selected.context_text && (
            <Typography.Paragraph type="secondary">
              上下文：{selected.context_text}
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
