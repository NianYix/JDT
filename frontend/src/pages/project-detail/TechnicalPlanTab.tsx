import { useCallback, useEffect, useState } from 'react'
import { Button, Form, Input, Select, Table, Typography, message } from 'antd'
import type { Project } from '../../api/projects'
import * as raApi from '../../api/requirementAnalyses'
import type { RequirementAnalysis } from '../../api/requirementAnalyses'
import * as tpApi from '../../api/technicalPlans'
import type { TechnicalPlan } from '../../api/technicalPlans'
import { ApiError } from '../../api/client'
import { RepoFilePicker } from '../../components/repo/RepoFilePicker'
import { StatusTag } from '../../components/workflow/StatusTag'
import { pollUntilTerminal } from '../../components/workflow/useWorkflowPolling'
import { ResultList, type JobSettledProps } from './shared'
import { useWorkspace } from '../../workspace/WorkspaceContext'

type Props = { project: Project } & JobSettledProps

export function TechnicalPlanTab({ project, onJobSettled }: Props) {
  const [form] = Form.useForm()
  const [plans, setPlans] = useState<TechnicalPlan[]>([])
  const [selected, setSelected] = useState<TechnicalPlan | null>(null)
  const [analyses, setAnalyses] = useState<RequirementAnalysis[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const { registerRunHandler } = useWorkspace()

  useEffect(() => {
    registerRunHandler(() => form.submit())
    return () => registerRunHandler(null)
  }, [form, registerRunHandler])

  const loadPlans = useCallback(async () => {
    const page = await tpApi.listTechnicalPlans(project.id)
    setPlans(page.items)
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
        const [planPage, analysisPage] = await Promise.all([
          tpApi.listTechnicalPlans(project.id),
          raApi.listRequirementAnalyses(project.id),
        ])
        setPlans(planPage.items)
        setSelected(planPage.items[0] ?? null)
        setAnalyses(analysisPage.items.filter((a) => a.status === 'succeeded'))
      } catch (err) {
        message.error(err instanceof ApiError ? err.message : '加载失败')
      }
    })()
  }, [project.id])

  const result = selected?.result_json

  return (
    <div>
      <Typography.Paragraph type="secondary">
        基于成功的需求分析、补充上下文或仓库文件生成技术规划。至少选择一项输入来源。
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={async (values: {
          requirement_analysis_id?: string
          context_text?: string
        }) => {
          const hasAnalysis = Boolean(values.requirement_analysis_id)
          const hasText = Boolean((values.context_text || '').trim())
          const hasFiles = selectedFiles.length > 0
          if (!hasAnalysis && !hasText && !hasFiles) {
            message.warning('请选择需求分析、填写补充上下文或勾选仓库文件')
            return
          }

          setSubmitting(true)
          try {
            const payload: tpApi.TechnicalPlanCreatePayload = {}
            if (hasAnalysis) {
              payload.requirement_analysis_id = values.requirement_analysis_id
            }
            if (hasText) {
              payload.context_text = values.context_text!.trim()
            }
            if (hasFiles) {
              payload.selected_files = selectedFiles
            }

            const created = await tpApi.createTechnicalPlan(project.id, payload)
            const final = await pollUntilTerminal({
              get: () => tpApi.getTechnicalPlan(project.id, created.id),
            })
            if (final.status === 'succeeded') {
              message.success('技术规划完成')
            } else {
              message.warning(final.error_message || '规划失败')
            }
            form.resetFields(['context_text'])
            setSelectedFiles([])
            await loadPlans()
            setSelected(final)
            onJobSettled?.()
          } catch (err) {
            message.error(err instanceof ApiError ? err.message : '规划请求失败')
          } finally {
            setSubmitting(false)
          }
        }}
      >
        <Form.Item name="requirement_analysis_id" label="关联需求分析（可选）">
          <Select
            allowClear
            placeholder={
              analyses.length ? '选择已成功的需求分析' : '暂无成功的需求分析'
            }
            options={analyses.map((a) => ({
              value: a.id,
              label: a.result_json?.summary || a.source_text.slice(0, 48),
            }))}
            disabled={!analyses.length}
          />
        </Form.Item>
        <Form.Item name="context_text" label="补充上下文（可选）">
          <Input.TextArea
            rows={5}
            placeholder="可补充技术约束、现有架构、团队技能栈等…"
          />
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
          生成技术规划
        </Button>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        历史记录
      </Typography.Title>
      <Table
        rowKey="id"
        size="small"
        dataSource={plans}
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
            render: (status: TechnicalPlan['status']) => <StatusTag status={status} />,
          },
          {
            title: '摘要',
            render: (_, row) =>
              row.result_json?.summary ||
              row.error_message ||
              row.context_text?.slice(0, 60) ||
              '基于需求分析',
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
          <Typography.Title level={5}>规划结果</Typography.Title>
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
                <strong>架构概览：</strong>
                {result.architecture_overview}
              </Typography.Paragraph>
              <ResultList title="技术栈" items={result.tech_stack} />
              {result.modules?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <Typography.Text strong>模块划分</Typography.Text>
                  <ul style={{ margin: '8px 0 0' }}>
                    {result.modules.map((m) => (
                      <li key={m.name}>
                        <strong>{m.name}</strong>：{m.responsibility}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <ResultList title="API 大纲" items={result.api_outline} />
              <ResultList title="数据模型大纲" items={result.data_model_outline} />
              <ResultList title="里程碑" items={result.milestones} />
              <ResultList title="依赖" items={result.dependencies} />
              <ResultList title="风险与缓解" items={result.risks_and_mitigations} />
              <ResultList title="待澄清问题" items={result.open_questions} />
            </>
          )}
          {selected.context_text && (
            <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
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
