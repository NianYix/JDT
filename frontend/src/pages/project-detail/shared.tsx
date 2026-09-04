import type { CSSProperties } from 'react'
import { Typography } from 'antd'

export function ResultList({ title, items }: { title: string; items?: string[] | null }) {
  if (!items?.length) {
    return null
  }
  return (
    <div style={{ marginBottom: 12 }}>
      <Typography.Text strong>{title}</Typography.Text>
      <ul style={{ margin: '8px 0 0' }}>
        {items.map((item) => (
          <li key={`${title}-${item}`}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export const codeBlockStyle: CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  padding: 12,
  borderRadius: 4,
  overflow: 'auto',
  fontSize: 13,
}

export type JobSettledProps = {
  onJobSettled?: () => void
}
