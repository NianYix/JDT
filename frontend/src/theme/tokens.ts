export type ThemeMode = 'dark' | 'light'

export type ColorTokens = {
  bgApp: string
  bgPanel: string
  bgElevated: string
  bgHover: string
  border: string
  borderStrong: string
  text: string
  textSecondary: string
  primary: string
  ai: string
  success: string
  warning: string
  error: string
  gridMinor: string
  gridMajor: string
}

export const darkColors: ColorTokens = {
  bgApp: '#0B0D10',
  bgPanel: '#15181E',
  bgElevated: '#181C22',
  bgHover: '#1C2129',
  border: '#252A32',
  borderStrong: '#303640',
  text: '#E6EAF0',
  textSecondary: '#8B949E',
  primary: '#5B8CFF',
  ai: '#8B7CFF',
  success: '#35C98B',
  warning: '#F5B942',
  error: '#FF5C68',
  gridMinor: 'rgba(230, 234, 240, 0.04)',
  gridMajor: 'rgba(230, 234, 240, 0.08)',
}

export const lightColors: ColorTokens = {
  bgApp: '#F4F6F8',
  bgPanel: '#FFFFFF',
  bgElevated: '#F8FAFC',
  bgHover: '#EEF1F5',
  border: '#E2E6EC',
  borderStrong: '#CBD2DC',
  text: '#1A1D23',
  textSecondary: '#6B7280',
  primary: '#3B6FE8',
  ai: '#6B5CE7',
  success: '#1FA971',
  warning: '#D97706',
  error: '#E11D48',
  gridMinor: 'rgba(26, 29, 35, 0.04)',
  gridMajor: 'rgba(26, 29, 35, 0.08)',
}

export const nodeKindColors = {
  system: '#8B949E',
  ai: '#8B7CFF',
  logic: '#5B8CFF',
  data: '#2DD4BF',
  action: '#F5B942',
} as const

export type NodeKind = keyof typeof nodeKindColors

export const motion = {
  fast: '150ms',
  panel: '280ms',
  easing: 'ease-out',
} as const

export const THEME_STORAGE_KEY = 'aec-theme'

export function colorsFor(mode: ThemeMode): ColorTokens {
  return mode === 'dark' ? darkColors : lightColors
}

export function applyCssVariables(mode: ThemeMode) {
  const c = colorsFor(mode)
  const root = document.documentElement
  root.dataset.theme = mode
  root.style.setProperty('--bg-app', c.bgApp)
  root.style.setProperty('--bg-panel', c.bgPanel)
  root.style.setProperty('--bg-elevated', c.bgElevated)
  root.style.setProperty('--bg-hover', c.bgHover)
  root.style.setProperty('--border', c.border)
  root.style.setProperty('--border-strong', c.borderStrong)
  root.style.setProperty('--text', c.text)
  root.style.setProperty('--text-secondary', c.textSecondary)
  root.style.setProperty('--accent-primary', c.primary)
  root.style.setProperty('--accent-ai', c.ai)
  root.style.setProperty('--success', c.success)
  root.style.setProperty('--warning', c.warning)
  root.style.setProperty('--error', c.error)
  root.style.setProperty('--grid-minor', c.gridMinor)
  root.style.setProperty('--grid-major', c.gridMajor)
  root.style.setProperty('--motion-fast', motion.fast)
  root.style.setProperty('--motion-panel', motion.panel)
}
