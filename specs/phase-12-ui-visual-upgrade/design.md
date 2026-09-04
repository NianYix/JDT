# AI Engineering Copilot — Phase 12 Design（UI 视觉升级）

> 基于已确认的 `requirements.md`（2026-08-31 拍板）  
> 状态：已与 requirements 对齐；`tasks.md` 已生成；待「开始执行」后实施

## 0. 已拍板决策

| # | 决策 |
|---|------|
| 1 | Canvas = **Pipeline 阶段节点 + SVG 连线**；**不**引入 React Flow |
| 2 | 默认 **Dark**；保留 **Light 切换** + `localStorage` 持久化 |
| 3 | 能力 UI = **选中节点 → 右侧 Inspector**；Tabs 降级/隐藏 |
| 4 | Top Bar **Run** = 仅触发**当前选中阶段**的既有创建入口 |
| 5 | 字体 = **Inter + JetBrains Mono**（npm 包或 `@fontsource`），系统回退 |

后端 / API：**零变更**。纯前端主题、壳层、项目工作区信息架构。

---

## 1. 架构概览

```text
App
├─ ThemeProvider (dark|light + persist)
│    └─ antd ConfigProvider (algorithm + component tokens)
├─ Auth routes (Login / Register) — 同 Token 暗/亮
└─ MainLayout (Workspace Shell)
     ├─ TopBar (项目上下文 / Undo·Redo 占位 / Run·Stop / AI / Theme / 状态)
     ├─ Body
     │    ├─ LeftRail (全局导航：Dashboard / Projects；项目内可切 Agent 摘要)
     │    ├─ MainPane
     │    │    ├─ 非项目页：Dashboard / ProjectList（Token 皮肤）
     │    │    └─ 项目页 ProjectWorkspace
     │    │         ├─ PipelineCanvas (grid + nodes + connections)
     │    │         └─ （可选）选中阶段简要上下文条
     │    └─ InspectorDrawer (右栏)
     │         ├─ stage = info → ProjectInfoTab
     │         └─ stage = AI → 对应 *Tab（表单/列表/结果）
     └─ StatusBar (ExecutionTimeline + 全局 Job 状态点)
```

**原则：** 各 `*Tab.tsx`、API、`pollUntilTerminal`、`RepoFilePicker` **业务逻辑原样复用**；变更集中在壳、主题、编排视图与呈现组件。

---

## 2. Design Token

### 2.1 文件结构

```text
frontend/src/theme/
  tokens.ts          # 色板、间距、半径、动效时长、节点类型色
  antdTheme.ts       # 由 tokens 生成 ConfigProvider theme
  ThemeContext.tsx   # mode: 'dark' | 'light'；toggle；localStorage key
  fonts.css          # Inter / JetBrains Mono 引入
```

`global.css` 改为消费 CSS 变量（由 `ThemeContext` 或 `:root[data-theme]` 注入）：

```css
:root[data-theme="dark"] {
  --bg-app: #0B0D10;
  --bg-panel: #15181E;
  --bg-elevated: #181C22;
  --border: #252A32;
  --border-strong: #303640;
  --text: #E6EAF0;
  --text-secondary: #8B949E;
  --accent-primary: #5B8CFF;
  --accent-ai: #8B7CFF;
  --success: #35C98B;
  --warning: #F5B942;
  --error: #FF5C68;
  /* … */
}
```

Light 主题提供**对应浅色 Token**（冷灰背景 `#F4F6F8` / 面板白偏冷 / 同系 Accent），结构类名不变，避免两套布局。

### 2.2 半径与阴影（克制）

- 控件半径：`4–8px`（禁止巨大圆角卡片墙）
- Shadow：仅 Hover / Selected 极淡；Selected 节点可用 `0 0 0 1px var(--accent-primary)` + 极轻 glow（`box-shadow: 0 0 0 1px …, 0 0 12px color-mix(...)` 透明度 ≤ 20%）

### 2.3 动效 Token

| Token | 值 |
|-------|-----|
| `--motion-fast` | 150ms |
| `--motion-panel` | 280ms |
| easing | `ease-out` |

---

## 3. Ant Design 集成

```tsx
<ConfigProvider
  locale={zhCN}
  theme={{
    algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: { colorPrimary, colorBgBase, colorBorder, fontFamily, borderRadius, … },
    components: { Layout, Menu, Tabs, Table, Button, Tag, … }
  }}
>
```

- 字体：`fontFamily: "'Inter', …"`；代码区 / 技术信息 class：`.mono { font-family: 'JetBrains Mono', ui-monospace, … }`
- 依赖建议：`@fontsource/inter`、`@fontsource/jetbrains-mono`（构建期打包，不依赖运行时 Google CDN；利于内网）

---

## 4. Layout 改造

### 4.1 从现状到目标

| 现状 | 目标 |
|------|------|
| `Sider(light)` + `Header` + 圆角白 `Content` | TopBar 通栏 + LeftRail 窄栏 + 无大圆角铺满工作区 + 底 StatusBar |
| 项目页 Title + Tabs | `ProjectWorkspace`：上 PipelineCanvas，右 Inspector |
| 登录浅色渐变 | Token 背景 + 居中面板，无装饰渐变 |

### 4.2 组件

| 组件 | 职责 |
|------|------|
| `layouts/MainLayout.tsx` | 壳组装；路由 `Outlet` |
| `layouts/TopBar.tsx` | 品牌/标题、Run/Stop、主题切换、用户、Connected 点 |
| `layouts/LeftRail.tsx` | Dashboard / Projects 图标导航 |
| `layouts/StatusBar.tsx` | 全局状态点 + 当前 Job 一行摘要 |
| `layouts/InspectorPanel.tsx` | 右侧可折叠栏（宽度 ~360–420px） |

### 4.3 Run / Stop 语义

- **Run**：`ProjectWorkspace` 暴露 `runSelectedStage()`；对 AI 阶段 → 滚动/聚焦 Inspector 内表单并可选 `form.submit()`（若表单未填则 focus 必填项 + message）；对 `info` 节点 → no-op 或提示「非执行节点」
- **Stop**：本阶段**无后端取消**；按钮在无 `running` 时 disabled；有 `running` 时仅 UI 提示「后端暂不支持取消」（符合 Phase 11 Out of Scope），避免假取消

---

## 5. Pipeline Canvas（非图编辑器）

### 5.1 阶段模型（前端常量）

```ts
type StageId =
  | 'info' | 'requirement' | 'technical' | 'coding'
  | 'testing' | 'review' | 'debugging' | 'metrics'

type StageDef = {
  id: StageId
  nodeId: string        // N-001 …
  title: string
  kind: 'system' | 'ai' | 'logic' | 'data' | 'action'
  tabComponent: …       // 懒加载既有 Tab
}
```

顺序与现 Tabs 一致；连接为**线性**（`i → i+1`），SVG path（二次/三次 Bezier）。

### 5.2 视觉

- 背景：CSS `background-image` 双层 radial/linear 点阵或细线 grid（major/minor 透明度极低）
- **PipelineNode**：顶栏 icon + name + kind；`N-00x` mono；状态点；可选最近 Job 一行
- **PipelineEdge**：默认 `--border-strong`；hover/active `--accent-primary`；error `--error`；running 时 CSS stroke-dashoffset 动画（克制）
- 选中：accent 边框 + 轻 glow

### 5.3 状态聚合

对各 AI 阶段：进入工作区或选中时 **懒加载** list API（复用现有 api 模块），取最新一条 Job 的 `status` 映射到节点：

| Job status | Node visual |
|------------|-------------|
| 无记录 | IDLE |
| pending / running | RUNNING |
| succeeded | COMPLETED |
| failed | ERROR |

不新增后端聚合接口。

### 5.4 文件

```text
frontend/src/workspace/
  stages.ts
  ProjectWorkspace.tsx
  PipelineCanvas.tsx
  PipelineNode.tsx
  PipelineEdge.tsx
  AgentControlPanel.tsx   # 可挂在 LeftRail 下部或 Inspector 顶
  ExecutionTimeline.tsx
  statusMap.ts
```

`ProjectDetailPage.tsx` 瘦身为加载 Project + 渲染 `ProjectWorkspace`。

---

## 6. Inspector 与 Tab 复用

```text
Inspector
  header: 节点名 + N-ID + StatusDot
  body: <SelectedTab project={project} />   // 原 *Tab 原样
```

- `destroyOnHidden` 等价：仅挂载当前选中阶段的 Tab，保持 Phase 11 懒加载行为
- Tab 内部样式：通过全局 Token / 少量 class 覆盖（如 `codeBlockStyle` 改为 CSS 变量），**避免改业务 handlers**
- `ProjectInfoTab` 同理放入 Inspector

可选轻改（非必须）：各 Tab 根节点加 `className="inspector-body"` 以便滚动与间距；不改 API 调用。

---

## 7. Agent Control + Execution Timeline

### 7.1 AgentControlPanel

当选中 AI 阶段且存在最新 Job：

```text
AGENT
● Running | Idle | Failed | …
派生步骤（前端映射，非后端推理链）：
  01 Queue / Accept     ✓|▶|○
  02 Invoke Model       ✓|▶|○
  03 Persist Result     ✓|▶|○
```

映射规则：`pending`→01▶；`running`→01✓ 02▶；`succeeded`→全✓；`failed`→当前步 ✕ + `error_message` 一行。

### 7.2 ExecutionTimeline

底栏或 Agent 下方：同上步骤列表紧凑版；随轮询更新。Tab 内 `pollUntilTerminal` 完成后，通过可选 callback / 简单事件（`CustomEvent` 或 Workspace Context）刷新节点状态与 Timeline——**优先 WorkspaceContext**：

```ts
type WorkspaceContextValue = {
  project: Project
  selectedStageId: StageId
  setSelectedStageId: …
  stageStatuses: Record<StageId, WorkflowStatus | 'idle'>
  refreshStageStatus: (id: StageId) => Promise<void>
  activeJob: { stageId; status; error?: string } | null
  requestRun: () => void  // TopBar Run 调用
}
```

Tab 内轮询成功后调用 `refreshStageStatus`（可在 Workspace 包一层薄 HOC，或先靠选中切换时重新 list，轮询中由 Tab 自己 UI 更新，Canvas 在 `submitting`/完成时由父级 `message` 后 refresh——实施时选**侵入最小**方案：Workspace 定时/聚焦 refresh + Tab 完成回调 prop 可选）。

**侵入最小推荐：** `ProjectWorkspace` 向各 Tab 传入可选 `onJobSettled?: () => void`；若改动 Tab 签名成本高，则 Workspace 在 `submitting` 无法感知时用 **选中阶段 list 轮询**（仅当 status 为 pending/running）。优先加 optional callback，改动面小。

---

## 8. Status 体系组件

| 组件 | 说明 |
|------|------|
| `StatusDot` | ● + 色；替代纯文字 |
| `StatusTag` | 升级为 Dot + 短标签；兼容原 `status` 字符串 |
| `statusMap.ts` | pending/running/succeeded/failed ↔ IDLE/RUNNING/… |

---

## 9. 页面级改造列表

| 文件 | 改造 |
|------|------|
| `App.tsx` | ThemeProvider + ConfigProvider theme |
| `main.tsx` | 引入 fonts.css |
| `styles/global.css` | Token 变量、壳层、grid、mono、动效 |
| `layouts/MainLayout.tsx` | 新壳 |
| `pages/LoginPage.tsx` / `RegisterPage.tsx` | 去渐变；Token 面板 |
| `pages/Dashboard.tsx` | 密度与文案层级；去仪表盘卡片感 |
| `pages/ProjectListPage.tsx` | 表格/工具条 Token 化 |
| `pages/ProjectDetailPage.tsx` | → Workspace |
| `pages/project-detail/*Tab.tsx` | 可选 `onJobSettled`；`codeBlockStyle` → token |
| `pages/project-detail/shared.tsx` | token 化 |
| `components/workflow/StatusTag.tsx` | Dot 风格 |
| `components/repo/RepoFilePicker.tsx` | 边框色改 Token |

---

## 10. 依赖

| 包 | 用途 | 必需 |
|----|------|------|
| `@fontsource/inter` | UI 字体 | 是 |
| `@fontsource/jetbrains-mono` | Mono | 是 |
| React Flow / XYFlow / D3 | — | **否** |
| framer-motion | — | **否**（CSS transition 足够） |

仅 `frontend` `package.json` 增加字体依赖。

---

## 11. 主题切换 UX

- TopBar 图标按钮：Sun / Moon 或「Dark/Light」
- `localStorage['aec-theme'] = 'dark' | 'light'`
- 首屏：读 storage，默认 `dark`
- `document.documentElement.dataset.theme = mode` 同步 CSS 变量

---

## 12. 风险与缓解

| 风险 | 缓解 |
|------|------|
| Tab 改签名影响大 | optional callback；无则 Canvas 依赖 list 刷新 |
| Light 变成「又一个 SaaS」 | Light Token 保持冷灰、细边框、同布局 |
| Inspector 表单过窄 | 宽度 400px+；复杂表单允许 Inspector 内纵向滚动；必要时加宽拖拽（本阶段固定宽度即可） |
| 动画过度 | 只用 Token 时长；流动动画仅 RUNNING 边 |

---

## 13. 实施顺序（与 tasks 对齐）

1. tokens + fonts + ThemeContext + antdTheme  
2. global.css + App 接入  
3. MainLayout / TopBar / LeftRail / StatusBar  
4. stages + PipelineCanvas/Node/Edge + ProjectWorkspace  
5. Inspector 挂载既有 Tabs  
6. AgentControl + ExecutionTimeline + StatusDot  
7. StatusTag / shared / RepoFilePicker 皮肤  
8. Login/Register/Dashboard/List 收尾  
9. 主题切换打磨 + 构建验收  

---

## 14. 验收映射

- 第一眼：Dark 专业工具壳 + Pipeline 中心  
- 第二眼：选中节点、右侧 Inspector、底栏/侧栏状态  
- 第三眼：RUNNING 边线流动 + Timeline 推进  
- 切换 Light 后结构不变  
- `npm run build` 通过；手动点通七类能力创建/轮询  
