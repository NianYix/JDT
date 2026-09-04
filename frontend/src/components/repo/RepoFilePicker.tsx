import { useEffect, useMemo, useState } from 'react'
import { Alert, Spin, Tree, Typography } from 'antd'
import type { DataNode } from 'antd/es/tree'
import { getRepoTree } from '../../api/repo'
import type { RepoTreeEntry } from '../../api/repo'
import { ApiError } from '../../api/client'

type RepoFilePickerProps = {
  projectId: string
  value: string[]
  onChange: (paths: string[]) => void
  disabled?: boolean
}

type TreeNode = DataNode & {
  isLeaf?: boolean
  children?: TreeNode[]
}

function buildTree(entries: RepoTreeEntry[]): TreeNode[] {
  type MutableNode = {
    title: string
    key: string
    isLeaf: boolean
    disableCheckbox: boolean
    childrenMap: Map<string, MutableNode>
  }

  const root = new Map<string, MutableNode>()

  const sorted = [...entries].sort((a, b) => a.path.localeCompare(b.path))

  for (const entry of sorted) {
    const parts = entry.path.split('/').filter(Boolean)
    let level = root
    let prefix = ''

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      prefix = prefix ? `${prefix}/${part}` : part
      const isLast = i === parts.length - 1
      let node = level.get(part)
      if (!node) {
        const isDir = isLast ? entry.is_dir : true
        node = {
          title: part,
          key: prefix,
          isLeaf: !isDir,
          disableCheckbox: isDir,
          childrenMap: new Map(),
        }
        level.set(part, node)
      }
      if (!isLast || entry.is_dir) {
        level = node.childrenMap
      }
    }
  }

  const toDataNodes = (map: Map<string, MutableNode>): TreeNode[] =>
    [...map.values()]
      .sort((a, b) => {
        if (a.isLeaf !== b.isLeaf) return a.isLeaf ? 1 : -1
        return String(a.title).localeCompare(String(b.title))
      })
      .map((node) => ({
        title: node.title,
        key: node.key,
        isLeaf: node.isLeaf,
        disableCheckbox: node.disableCheckbox,
        children: node.childrenMap.size > 0 ? toDataNodes(node.childrenMap) : undefined,
      }))

  return toDataNodes(root)
}

export function RepoFilePicker({
  projectId,
  value,
  onChange,
  disabled,
}: RepoFilePickerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [entries, setEntries] = useState<RepoTreeEntry[]>([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const tree = await getRepoTree(projectId)
        if (!cancelled) {
          setEntries(tree.entries)
        }
      } catch (err) {
        if (!cancelled) {
          setEntries([])
          setError(
            err instanceof ApiError
              ? err.message
              : '无法加载仓库文件树（请先配置工作区路径）',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [projectId])

  const treeData = useMemo(() => buildTree(entries), [entries])

  if (loading) {
    return <Spin size="small" tip="加载仓库文件…" />
  }

  if (error) {
    return (
      <Alert
        type="warning"
        showIcon
        message="仓库文件不可用"
        description={error}
      />
    )
  }

  if (!treeData.length) {
    return (
      <Typography.Text type="secondary">工作区为空或无可选文件</Typography.Text>
    )
  }

  return (
    <div>
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        勾选要附加到 AI 上下文的文件（不可选目录）
      </Typography.Text>
      <Tree
        checkable
        checkStrictly
        defaultExpandAll={treeData.length <= 40}
        disabled={disabled}
        treeData={treeData}
        checkedKeys={value}
        onCheck={(checked) => {
          const keys = Array.isArray(checked) ? checked : checked.checked
          onChange(keys.map(String))
        }}
        style={{ maxHeight: 280, overflow: 'auto', border: '1px solid var(--border)', padding: 8, borderRadius: 4, background: 'var(--bg-elevated)' }}
      />
    </div>
  )
}
