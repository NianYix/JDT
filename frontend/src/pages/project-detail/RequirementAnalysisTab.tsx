import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as raApi from '../../api/requirementAnalyses'
import type { RequirementAnalysis } from '../../api/requirementAnalyses'
import { ApiError } from '../../api/client'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function RequirementAnalysisTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [analyses, setAnalyses] = useState<RequirementAnalysis[]>([])
  const [selected, setSelected] = useState<RequirementAnalysis | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const load = useCallback(async () => {
    const page = await raApi.listRequirementAnalyses(project.id)
    setAnalyses(page.items)
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
        await load()
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
      }
    })()
  }, [load])

  const result = selected?.result_json

  return (
    <div>
      <Typography.Paragraph type="secondary">
        粘贴需求原文后提交。需在 Backend 配置有效的 `LLM_API_KEY`（OpenAI 兼容）。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: { source_text: string }) => {
          setSubmitting(true)
          try {
            const created = await raApi.createRequirementAnalysis(
              project.id,
              values.source_text,
            )
            const final = await pollUntilTerminal({
              get: () => raApi.getRequirementAnalysis(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('分析完成')
            } else {
              message.warning(final.error_message || '分析失败')
            }
            form.resetFields()
            await load()
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
          name="source_text"
          label="需求原文"
          rules={[{ required: true, message: '请输入需求文本' }]}
        >
          <Input.TextArea rows={6} placeholder="在此粘贴产品/业务需求描述…" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={submitting}>
          开始分析
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={analyses}
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
            render: (status: RequirementAnalysis['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary || row.error_message || row.source_text.slice(0, 60),
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
        <div style={{ marginTop: 24, maxWidth: 720 }}>
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
              <ResultList title="目标" items={result.goals} />
              <ResultList title="干系人" items={result.stakeholders} />
              <ResultList title="功能需求" items={result.functional_requirements} />
              <ResultList title="非功能需求" items={result.non_functional_requirements} />
              <ResultList title="假设" items={result.assumptions} />
              <ResultList title="风险" items={result.risks} />
              <ResultList title="待澄清问题" items={result.open_questions} />
            </>
          )}
          <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
            原文：{selected.source_text}
          </Typography.Paragraph>
        </div>
      )}
    </div>
  )
}
