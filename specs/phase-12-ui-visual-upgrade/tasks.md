# AI Engineering Copilot — Phase 12 Tasks（UI 视觉升级）

> 状态：已完成（2026-08-31）  
> 决策回放：Pipeline 隐喻（无 React Flow）；默认 Dark + Light 切换；Inspector 承载 Tab；Run=当前阶段；Inter + JetBrains Mono

## 进度总览

| ID | 任务 | 状态 |
|----|------|------|
| T1 | Design Token + 字体 + ThemeContext | 完成 |
| T2 | Ant Design 主题接入 + global.css | 完成 |
| T3 | App Shell（TopBar / LeftRail / StatusBar） | 完成 |
| T4 | Pipeline 阶段模型 + Canvas / Node / Edge | 完成 |
| T5 | ProjectWorkspace + Inspector 挂载既有 Tab | 完成 |
| T6 | Agent Control + Execution Timeline + Status 体系 | 完成 |
| T7 | TopBar Run/主题切换与 Workspace 联通 | 完成 |
| T8 | 登录/注册/Dashboard/项目列表皮肤收尾 | 完成 |
| T9 | Tab 轻适配（token / onJobSettled）+ 构建验收 | 完成 |

---

## T1 — Design Token + 字体 + ThemeContext

- [ ] 新增 `frontend/src/theme/tokens.ts`（dark/light 色板、节点类型色、motion）
- [ ] 新增 `frontend/src/theme/ThemeContext.tsx`（mode、toggle、`localStorage['aec-theme']`、`data-theme`）
- [ ] 安装并引入 `@fontsource/inter`、`@fontsource/jetbrains-mono`（或等价），新增 `fonts.css`
- [ ] 系统字体回退栈写清

**验收：** 切换 mode 时 `document.documentElement.dataset.theme` 变化；刷新后偏好保持。

---

## T2 — Ant Design 主题 + global.css

- [ ] 新增 `frontend/src/theme/antdTheme.ts`，按 mode 返回 `theme` 配置（darkAlgorithm / defaultAlgorithm）
- [ ] `App.tsx`：ThemeProvider 包裹 ConfigProvider，注入 `locale` + `theme`
- [ ] 重写 `styles/global.css`：CSS 变量、壳层 class、`.mono`、grid 工具类、禁止大面积装饰渐变
- [ ] 移除/替换旧浅色硬编码（`.app-content` 白卡片等）

**验收：** 任意页 Ant Design 组件与壳层同色系；无大面积 `#000` 纯黑底。

---

## T3 — App Shell

- [ ] 拆分 `TopBar` / `LeftRail` / `StatusBar`（可同目录 `layouts/`）
- [ ] 重构 `MainLayout.tsx`：通栏顶栏 + 左轨 + 主区 Outlet + 底栏；去掉 light Sider 旧结构
- [ ] TopBar：品牌/标题区、主题切换按钮、用户与退出、● Connected 占位
- [ ] LeftRail：Dashboard / Projects 导航（图标+可选文字）

**验收：** 路由与鉴权不变；桌面布局符合 design §4。

---

## T4 — Pipeline Canvas

- [ ] 新增 `workspace/stages.ts`（N-001…、kind、标题、与旧 tab key 对齐）
- [ ] `PipelineNode` / `PipelineEdge` / `PipelineCanvas`（淡网格 + SVG 连线 + 选中态）
- [ ] RUNNING 连线克制 dash 动画；选中 accent 边框 + 极轻 glow
- [ ] 节点展示 mono Node ID + StatusDot

**验收：** 八个阶段线性可视；点击切换选中；无图编辑器依赖。

---

## T5 — ProjectWorkspace + Inspector

- [ ] `ProjectWorkspace.tsx` + `WorkspaceContext`（selectedStage、stageStatuses、refresh、requestRun）
- [ ] `ProjectDetailPage` 改为加载 project 后渲染 Workspace
- [ ] 右侧 `InspectorPanel`：header（名/ID/状态）+ 当前阶段既有 `*Tab` 懒挂载
- [ ] 隐藏原水平 Tabs 主导航（能力改由 Pipeline 选择）

**验收：** 选中各节点可操作原表单/列表/轮询/结果；`RepoFilePicker` 仍可用。

---

## T6 — Agent Control + Timeline + Status

- [ ] `StatusDot` + 升级 `StatusTag`（映射 pending/running/succeeded/failed）
- [ ] `AgentControlPanel`：前端三步映射（Queue → Invoke → Persist），非聊天 UI
- [ ] `ExecutionTimeline` 接入 StatusBar 或 Agent 区
- [ ] 阶段状态：进入/选中时 list 最新 Job；running 时短轮询刷新节点

**验收：** 执行中 Timeline 推进；第一眼能区分 Idle/Running/完成/失败。

---

## T7 — Run / 主题与壳联通

- [ ] TopBar **Run**：调用 `requestRun` → 聚焦 Inspector；AI 阶段尝试触发表单提交或聚焦必填
- [ ] **Stop**：无后端取消 → running 时提示不可取消 / disabled 策略按 design
- [ ] 主题切换在 TopBar 可用且全页即时生效
- [ ] StatusBar 显示当前 activeJob 一行摘要

**验收：** Run 只作用于当前选中阶段；Light/Dark 结构一致。

---

## T8 — 认证页与列表页收尾

- [ ] `LoginPage` / `RegisterPage`：去装饰渐变；Token 面板
- [ ] `Dashboard` / `ProjectListPage`：专业工具密度与边框层级，避免仪表盘卡片堆砌
- [ ] `shared.tsx` `codeBlockStyle`、`RepoFilePicker` 边框改 CSS 变量

**验收：** 未登录/列表路径视觉统一；禁区风格未出现。

---

## T9 — Tab 轻适配 + 验收

- [ ] 各 AI Tab 可选 `onJobSettled`（或等价）通知 Workspace 刷新节点状态
- [ ] `npm run build` 通过；`oxlint` 无新增阻断问题
- [ ] 手动清单：登录 → 项目 → 七阶段各打开 → 至少一类 AI 创建并见 RUNNING→终态 → 切 Light → 再切回 Dark

**验收：** requirements §6 检查项通过；无业务回归。

---

## 依赖任务顺序

```text
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9
         ↘（T8 可与 T5–T7 部分并行，但建议壳稳定后再收尾）
```

---

回复 **「开始执行」** 后按 T1→T9 改代码。
