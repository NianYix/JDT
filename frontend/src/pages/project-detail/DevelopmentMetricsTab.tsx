import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as dmApi from '../../api/developmentMetrics'
import type { DevelopmentMetric } from '../../api/developmentMetrics'
import { ApiError } from '../../api/client'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function DevelopmentMetricsTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [metrics, setMetrics] = useState<DevelopmentMetric[]>([])
  const [selected, setSelected] = useState<DevelopmentMetric | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadList = useCallback(async () => {
    const page = await dmApi.listDevelopmentMetrics(project.id)
    setMetrics(page.items)
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
        await loadList()
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
      }
    })()
  }, [loadList])

  const result = selected?.result_json

  return (
    <div>
      <Typography.Paragraph type="secondary">
        描述度量关注点；系统将自动汇总本项目 AI 工作流记录（各阶段数量与摘要）并生成报告。非 Git/CI 真实指标。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: { metrics_focus: string; context_text?: string }) => {
          const focus = (values.metrics_focus || '').trim()
          if (!focus) {
            message.warning('请输入度量关注点')
            return
          }

          setSubmitting(true)
          try {
            const payload: dmApi.DevelopmentMetricCreatePayload = { metrics_focus: focus }
            const ctx = (values.context_text || '').trim()
            if (ctx) {
              payload.context_text = ctx
            }

            const created = await dmApi.createDevelopmentMetric(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => dmApi.getDevelopmentMetric(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('度量报告生成完成')
            } else {
              message.warning(final.error_message || '生成失败')
            }
            form.resetFields(['context_text'])
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
          name="metrics_focus"
          label="度量关注点"
          rules={[{ required: true, message: '请输入度量关注点' }]}
        >
          <Input.TextArea
            rows={3}
            placeholder="例如：评估本项目 AI 研发流程健康度与薄弱环节…"
          />
        </Form.Item>
        <Form.Item name="context_text" label="团队/流程补充（可选）">
          <Input.TextArea rows={4} placeholder="团队规模、迭代节奏、质量目标等…" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={submitting}>
          生成度量报告
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={metrics}
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
            render: (status: DevelopmentMetric['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary || row.error_message || row.metrics_focus.slice(0, 60),
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
          <Typography.Title level={5}>报告结果</Typography.Title>
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
                <strong>整体健康度：</strong>
                {result.overall_health}
              </Typography.Paragraph>
              {result.workflow_coverage?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>工作流覆盖</Typography.Text>
                  <Table
                    rowKey="stage"
                    size="small"
                    pagination={false}
                    style={{ marginTop: 8 }}
                    dataSource={result.workflow_coverage}
                    columns={[
                      { title: '阶段', dataIndex: 'stage', width: 180 },
                      { title: '状态', dataIndex: 'status', width: 100 },
                      { title: '说明', dataIndex: 'notes' },
                    ]}
                  />
                </div>
              )}
              {result.quality_indicators?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>质量指标</Typography.Text>
                  <Table
                    rowKey="name"
                    size="small"
                    pagination={false}
                    style={{ marginTop: 8 }}
                    dataSource={result.quality_indicators}
                    columns={[
                      { title: '名称', dataIndex: 'name', width: 160 },
                      { title: '评估', dataIndex: 'assessment' },
                      { title: '依据', dataIndex: 'evidence' },
                    ]}
                  />
                </div>
              )}
              <ResultList title="效率指标" items={result.velocity_indicators} />
              <ResultList title="风险信号" items={result.risk_indicators} />
              <ResultList title="改进建议" items={result.recommendations} />
              <ResultList title="待澄清问题" items={result.open_questions} />
            </>
          )}
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            关注点：{selected.metrics_focus}
          </Typography.Paragraph>
          {selected.context_text && (
            <Typography.Paragraph type="secondary">
              补充：{selected.context_text}
            </Typography.Paragraph>
          )}
        </div>
      )}
    </div>
  )
}
