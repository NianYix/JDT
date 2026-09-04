export function StatusDot({
  visual,
  title,
}: {
  visual: 'idle' | 'running' | 'completed' | 'error' | 'warning'
  title?: string
}) {
  return <span className={`status-dot ${visual}`} title={title} aria-hidden />
}
