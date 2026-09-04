const TERMINAL = new Set(['succeeded', 'failed'])

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function pollUntilTerminal<T extends { status: string }>(options: {
  get: () => Promise<T>
  intervalMs?: number
  maxAttempts?: number
}): Promise<T> {
  const intervalMs = options.intervalMs ?? 1500
  const maxAttempts = options.maxAttempts ?? 80

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const current = await options.get()
    if (TERMINAL.has(current.status)) {
      return current
    }
    if (attempt < maxAttempts - 1) {
      await sleep(intervalMs)
    }
  }

  throw new Error('轮询超时：任务仍未完成')
}
