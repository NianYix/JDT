import { theme, type ThemeConfig } from 'antd'
import { colorsFor, type ThemeMode } from './tokens'

const fontFamily =
  "'Inter', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif"

export function buildAntdTheme(mode: ThemeMode): ThemeConfig {
  const c = colorsFor(mode)
  return {
    algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: c.primary,
      colorSuccess: c.success,
      colorWarning: c.warning,
      colorError: c.error,
      colorInfo: c.primary,
      colorBgBase: c.bgApp,
      colorBgContainer: c.bgPanel,
      colorBgElevated: c.bgElevated,
      colorBorder: c.border,
      colorBorderSecondary: c.borderStrong,
      colorText: c.text,
      colorTextSecondary: c.textSecondary,
      fontFamily,
      borderRadius: 6,
      wireframe: false,
    },
    components: {
      Layout: {
        headerBg: c.bgPanel,
        bodyBg: c.bgApp,
        siderBg: c.bgPanel,
        triggerBg: c.bgElevated,
      },
      Menu: {
        itemBg: 'transparent',
        subMenuItemBg: c.bgElevated,
        itemSelectedBg: c.bgHover,
        itemHoverBg: c.bgHover,
      },
      Table: {
        headerBg: c.bgElevated,
        rowHoverBg: c.bgHover,
      },
      Card: {
        colorBgContainer: c.bgPanel,
      },
      Button: {
        primaryShadow: 'none',
      },
      Tabs: {
        itemSelectedColor: c.primary,
        inkBarColor: c.primary,
      },
    },
  }
}
