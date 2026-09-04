# AI Engineering Copilot — Phase 12 Requirements（UI 视觉升级：Dark Professional Technical Workspace）

> 来源：`UI_Optimize.txt`  
> 前置：Phase 1–11 已完成（七大 AI 能力 + 异步任务 / 工作流抽象 / 仓库上下文）  
> 目标：将前端从「普通浅色 SaaS 后台」升级为「AI Native + Developer Tool」专业工作台视觉语言  
> 状态：**已确认**（2026-08-31；待确认问题已拍板，见 §5）

---

## 1. 背景与目标

### 1.1 当前 UI 问题分析（基于现状）

| 维度 | 现状 | 问题 |
|------|------|------|
| 主题 | 浅色 Ant Design 默认（`#f5f7fa` / 白卡片） | 像普通后台，缺少工程工具感 |
| 布局 | 左侧 Sider + 顶栏 + 居中圆角 Content | SaaS Dashboard 布局，非 IDE / Workspace |
| 工作区 | 项目详情为水平 Tabs + 表单列表 | 无「逻辑流 / 执行中心」视觉焦点 |
| 状态 | `StatusTag` 使用 Ant Design 默认 Tag 色 | 状态体系弱，难以感知「系统正在运行」 |
| Agent / AI | 各 Tab 表单提交 + 轮询结果 | 像 CRUD 表单，不像 Agent 在操作工程图 |
| 字体 | Segoe UI / 系统中文栈 | 无 Mono 技术信息层级 |
| 动效 | 几乎无克制动效 | 状态切换静态 |
| 装饰风险 | 登录页已有浅色渐变背景 | 需避免升级成「AI 紫渐变 / Glow 特效」 |

### 1.2 设计定位（验收标准）

整体定位：**AI Native + Developer Tool + Logic Flow + Professional Workspace**

第一眼应像专业 AI 工程工具；第二眼能识别当前项目 / 能力流 / 执行状态 / 选中上下文；第三眼能感到「系统在运行」。

科技感来自：**信息层级、精细边框、状态色、结构布局、微交互** —— 而非大量 Glow / 霓虹 / 渐变。

### 1.3 In Scope

1. **Design Token + Global Dark Theme**（含 Ant Design `ConfigProvider` 暗色算法）
2. **App Shell / Layout 重构**：Top Bar + 工作区（左导航 / 主内容 / 可选右 Inspector）+ 底栏状态区
3. **项目工作区视觉升级**：七大能力不再仅呈现为「普通 Tabs 表单」，引入 **Logic Flow / Pipeline** 视觉主轴（阶段节点 + 连线隐喻），在**不引入完整图编辑器依赖**的前提下完成
4. **Execution / Status 体系**：IDLE / RUNNING / COMPLETED / WARNING / ERROR 视觉语言；执行时间线
5. **Agent / Job 运行态面板**：以 Control Center（Planning / Reasoning / Action / Validation 式信息层级）呈现异步 Job，而非聊天窗
6. **Toolbar**：IDE 风格顶栏（项目、Run/Stop 语义入口、连接/模型/资源占位）
7. **Typography**：UI 用 Inter（或等价无衬线）；Node ID / 状态码 / 延迟等用 Monospace
8. **微交互**：Hover / Selected / Panel 过渡 100–400ms；执行态轻微呼吸与克制流动暗示
9. **登录 / 注册页**同步暗色专业风格（禁止赛博朋克装饰）

### 1.4 Out of Scope（本阶段明确不做）

- 引入完整节点图编辑器（React Flow / XYFlow 等）作为独立产品能力（可列为后续 Phase）
- 可拖拽连线、节点增删改、数据端口编排等**新业务功能**
- 真实系统 CPU / Memory 遥测（顶栏可显示占位或前端可获得的静态/ mock 信息，不做 OS 级采集）
- 后端 API / 数据模型变更（纯前端视觉与信息架构；除非为展示已有字段）
- 玻璃拟态 everywhere、霓虹 Glow、星空/电路板背景、大面积蓝紫渐变
- 重写业务逻辑、破坏现有七类 AI CRUD / 轮询行为
- 一次性重写全部页面后无法回退（须分模块、可渐进合入）

### 1.5 范围边界说明（文档理想态 vs 本阶段落地）

`UI_Optimize.txt` 描述了完整 Logic Canvas / Bezier 连线粒子 / Agent 改图等理想态。本阶段将其**映射到现有产品**：

| 文档概念 | 本阶段落地 |
|----------|------------|
| Logic Canvas | 项目工作区中心：**阶段 Pipeline / Flow 视图**（七大能力 + 执行态），非自由画布编辑器 |
| Node | **阶段 / Job 卡片节点**（类型色、ID、状态、关键摘要） |
| Connection | **阶段间 Bezier/折线 + 执行路径高亮**（克制动效） |
| Agent Panel | **左侧或侧栏 Job / Agent Control**（当前运行 Job 的步骤态） |
| Inspector | **右侧上下文**：选中阶段/Job 的详情、结果、参数 |
| Execution Timeline | **底栏或侧栏**：步骤列表 + 状态点 |
| Canvas Grid | Pipeline / 主工作区淡网格背景 |

完整自由画布编辑器留待后续 Phase，不阻塞本阶段视觉升级。

---

## 2. 功能需求（EARS）

### 2.1 Design Token 与主题

**REQ-THEME-001**  
WHEN 应用加载时，THE SYSTEM SHALL 通过统一 Design Token（CSS 变量和/或主题配置）提供背景、面板、边框、主/次文本、Primary / AI / Success / Warning / Error 色值，且全局 UI 消费这些 Token 而非散落硬编码色值。

**REQ-THEME-002**  
WHEN 应用处于默认工作主题时，THE SYSTEM SHALL 呈现 Dark Professional Technical UI（深黑/深灰/石墨/冷灰为主），且不得以大面积纯黑 `#000000` 作为主背景。

**REQ-THEME-002a**  
WHEN 用户切换主题时，THE SYSTEM SHALL 支持在 Dark 与 Light 专业主题之间切换，并持久化用户偏好（如 `localStorage`）；Light 主题须保持同一信息架构与组件结构，仅替换 Token，不得退回「普通 SaaS 白卡片仪表盘」观感。

**REQ-THEME-003**  
WHEN 主题色被应用时，THE SYSTEM SHALL 将 Primary 定位为克制科技色（推荐 `#5B8CFF`）、AI 色（推荐 `#8B7CFF`），Success / Warning / Error 分别对应文档推荐色或等价 Token，且不得在全局大面积使用霓虹 Glow 或蓝紫渐变作为主视觉。

**REQ-THEME-004**  
WHEN Ant Design 组件渲染时，THE SYSTEM SHALL 通过 `ConfigProvider`（或等价机制）应用与 Design Token 一致的暗色算法与组件 token，保证 Button / Tabs / Table / Form / Menu / Tag 等与壳层风格统一。

**REQ-THEME-005**  
WHEN 登录与注册页展示时，THE SYSTEM SHALL 使用与工作台一致的暗色专业风格，且不得使用赛博朋克、星空、电路板或大面积装饰性渐变背景。

### 2.2 布局与信息架构

**REQ-LAYOUT-001**  
WHEN 已认证用户进入应用壳层时，THE SYSTEM SHALL 提供专业开发工具式布局，至少包含：Top Bar、主工作区、以及可识别的状态/执行区域（底栏或等价位置）。

**REQ-LAYOUT-002**  
WHEN 用户位于项目工作区时，THE SYSTEM SHALL 将 **Logic Flow / Pipeline 主区** 作为视觉中心，左侧为导航或 Agent/Flow 控制，右侧为 Inspector/Context（可默认折叠），且主区不得再表现为「居中大圆角白卡片仪表盘」。

**REQ-LAYOUT-003**  
WHEN 用户在壳层导航时，THE SYSTEM SHALL 保留既有路由能力（Dashboard、项目列表、项目详情及七大能力入口），不得因布局重构导致路由或鉴权失效。

**REQ-LAYOUT-004**  
WHEN 视口宽度变化时，THE SYSTEM SHALL 保证主布局在桌面可用；窄屏下允许折叠侧栏/Inspector，但不得破坏核心操作可达性。

### 2.3 Logic Flow / Pipeline（映射 Canvas）

**REQ-FLOW-001**  
WHEN 用户打开项目详情工作区时，THE SYSTEM SHALL 展示可识别的逻辑流程主视图（阶段节点序列或等价 Pipeline），表达「能力阶段 → 连接 → 状态 → 执行」关系，而非仅水平 Tabs + 表单堆叠。

**REQ-FLOW-002**  
WHEN 流程节点渲染时，THE SYSTEM SHALL 展示节点标识（图标/名称/类型）、工程化 Node ID（如 `N-001` 风格）、以及执行状态指示。

**REQ-FLOW-003**  
WHEN 不同能力/节点类型展示时，THE SYSTEM SHALL 使用克制的类型色区分（例如 AI / Logic / Data / Action / System 映射到紫/蓝/青/黄/灰），且不得依赖大面积填充或强 Glow。

**REQ-FLOW-004**  
WHEN 用户选中某一阶段节点时，THE SYSTEM SHALL 以 Accent 边框 + 极轻微外发光（可选）标识选中态，并将该节点上下文反映到 Inspector 或主内容区，且不得用大面积 Accent 填充整卡。

**REQ-FLOW-005**  
WHEN 流程主区背景渲染时，THE SYSTEM SHALL 使用非常淡的网格（可含 major/minor），强度以不干扰节点阅读为准。

**REQ-FLOW-006**  
WHEN 用户从流程节点进入某能力时，THE SYSTEM SHALL 仍可使用既有业务组件完成创建/列表/轮询/结果展示，不得为视觉重构破坏现有 API 调用与状态机。

### 2.4 Connection / 连线

**REQ-CONN-001**  
WHEN 阶段节点之间存在顺序/依赖关系时，THE SYSTEM SHALL 使用曲线或折线连接（优先 Bezier 风格），而非纯静态无语义灰直线且无状态区分。

**REQ-CONN-002**  
WHEN 用户 Hover 连接或连接处于当前执行路径时，THE SYSTEM SHALL 高亮该连接；执行中路径可使用 Accent，错误路径使用 Error 色。

**REQ-CONN-003**  
WHEN 流程处于执行中时，THE SYSTEM SHALL 允许沿连接呈现克制的数据流动画（粒子或短划线移动），动画须服务于状态表达且不得持续喧宾夺主。

### 2.5 Agent / Job Control

**REQ-AGENT-001**  
WHEN 存在进行中的 AI Job（`pending` / `running`）时，THE SYSTEM SHALL 在 Agent/控制区域以「Control Center」信息层级展示运行态（例如状态点 + Planning/Action/Validation 式步骤摘要），而不得表现为通用聊天对话窗口。

**REQ-AGENT-002**  
WHEN 无进行中 Job 时，THE SYSTEM SHALL 在该区域展示 IDLE 或最近一次执行摘要，保持面板结构稳定。

**REQ-AGENT-003**  
WHEN Agent/控制区展示步骤时，THE SYSTEM SHALL 优先复用既有 Job 状态与结果字段，不得虚构后端未提供的推理链内容；若后端无细粒度步骤，THE SYSTEM SHALL 用前端可推导的阶段映射（排队 → 调用 → 落库 → 完成/失败）表达。

### 2.6 Execution / Runtime 状态

**REQ-EXEC-001**  
WHEN 工作流或 Job 状态变更时，THE SYSTEM SHALL 使用统一状态视觉语言至少覆盖：IDLE、RUNNING、COMPLETED、WARNING、ERROR（或与现有 `pending`/`running`/`succeeded`/`failed` 的明确映射）。

**REQ-EXEC-002**  
WHEN 状态指示展示时，THE SYSTEM SHALL 优先使用状态点（● 等）配合短标签，避免仅靠大段文字描述状态。

**REQ-EXEC-003**  
WHEN 执行过程可见时，THE SYSTEM SHALL 提供 Execution Timeline（步骤列表 + 完成/进行中/未开始标记），并随轮询结果推进。

**REQ-EXEC-004**  
WHEN 节点处于 RUNNING 时，THE SYSTEM SHALL 允许极轻微的边框呼吸或等价动效；COMPLETED / ERROR 须瞬时可辨且动效克制。

### 2.7 Toolbar

**REQ-TOOL-001**  
WHEN Top Bar 渲染时，THE SYSTEM SHALL 采用 IDE/专业工具风格分组（项目上下文、编辑/历史占位或可用操作、Run/Stop 语义、AI/Debug 入口），避免堆叠大量普通无分组 Button。

**REQ-TOOL-002**  
WHEN Top Bar 右侧展示时，THE SYSTEM SHALL 提供连接/会话状态指示（如 ● Connected）及模型或环境信息展示位；资源占用（CPU/Memory）若无真实数据可省略或标注为占位，不得伪造误导性精确遥测。

**REQ-TOOL-003**  
WHEN 用户触发与现有能力相关的 Run 类操作时，THE SYSTEM SHALL 路由到当前选中阶段的既有创建/执行流程，不得发明无后端支持的全局「一键跑全流程」除非明确另开需求。

### 2.8 Typography 与技术信息

**REQ-TYPE-001**  
WHEN 普通 UI 文案渲染时，THE SYSTEM SHALL 使用 Inter 或项目选定的专业无衬线字体，不得使用花哨装饰字体。

**REQ-TYPE-002**  
WHEN 展示 Node ID、Execution ID、参数名、延迟、Token 类技术信息时，THE SYSTEM SHALL 使用 Monospace（JetBrains Mono / Geist Mono / SF Mono 或等价 web 字体）。

### 2.9 微交互与动效

**REQ-MOTION-001**  
WHEN 可交互元素被 Hover 时，THE SYSTEM SHALL 提供细微的背景/边框/阴影或 Accent 反馈，时长约 100–200ms。

**REQ-MOTION-002**  
WHEN 面板打开或 Inspector 切换时，THE SYSTEM SHALL 使用约 200–400ms 的克制过渡。

**REQ-MOTION-003**  
WHEN 添加任何动画时，THE SYSTEM SHALL 确保动画服务于状态变化、数据流或执行过程，不得为装饰而动画。

### 2.10 禁止事项（负面需求）

**REQ-FORBID-001**  
THE SYSTEM SHALL NOT 以大面积蓝紫渐变、霓虹 Glow、巨大圆角卡片墙、玻璃拟态铺满、赛博朋克/星空/电路板背景、或「AI 生成站常见紫色渐变」作为主视觉语言。

**REQ-FORBID-002**  
THE SYSTEM SHALL NOT 为追求视觉效果而破坏既有业务功能、鉴权、异步轮询或仓库文件选择行为。

**REQ-FORBID-003**  
THE SYSTEM SHALL NOT 一次性无模块边界地重写整个前端；实施须按 Token → Theme → Layout → Flow → Node/Conn → Agent → Inspector → Toolbar → Timeline → Status → Micro Interaction 的优先序推进。

### 2.11 复用与质量

**REQ-QA-001**  
WHEN 视觉组件被改造时，THE SYSTEM SHALL 尽可能复用现有业务组件与 API 模块（各 `*Tab.tsx`、`StatusTag`、`RepoFilePicker`、workflow polling 等），以皮肤/壳层/编排视图包裹为主。

**REQ-QA-002**  
WHEN 前端构建时，THE SYSTEM SHALL 保持 `frontend` 的 TypeScript 构建与既有 lint 可通过（不引入未使用的重型依赖，除非 design 阶段明确批准）。

---

## 3. 推荐 Design Token（草案，design 阶段定稿）

```
Background:  #0B0D10 / #0F1115 / #14171C
Panel:       #15181E / #181C22
Border:      #252A32 / #303640
Text:        #E6EAF0
Secondary:   #8B949E
Primary:     #5B8CFF
AI:          #8B7CFF
Success:     #35C98B
Warning:     #F5B942
Error:       #FF5C68
```

节点类型色（克制描边/图标色，非大面积填充）：

| 类型映射（示例） | 色相 |
|------------------|------|
| AI 能力节点 | 紫（AI） |
| Logic / 分析 | 蓝（Primary） |
| Data / 度量 | 青 |
| Action / 编码·测试 | 黄（Warning 系） |
| System / 项目信息 | 灰 |

---

## 4. 实施顺序（确认后写入 tasks.md）

1. Design Token  
2. Global Theme（含 Ant Design）  
3. Layout（App Shell）  
4. Canvas / Pipeline 主区  
5. Node（阶段卡片）  
6. Connection  
7. Agent Panel  
8. Inspector  
9. Toolbar  
10. Execution Timeline  
11. Status System  
12. Micro Interaction  

优先级：**信息架构 > 布局 > 层级 > 状态 > 交互 > 装饰**

---

## 5. 已拍板决策（2026-08-31）

| # | 问题 | 决策 |
|---|------|------|
| 1 | Canvas 深度 | **Pipeline / 阶段节点 + 连线隐喻**；不引入 React Flow 等图编辑器库 |
| 2 | 主题 | **默认 Dark**；**保留 Light 切换**并持久化偏好 |
| 3 | 七大能力入口 | **主区选中节点 + 右侧 Inspector** 承载表单与结果；水平 Tabs 降级/隐藏 |
| 4 | 顶栏 Run | **仅对当前选中阶段**触发既有创建/执行；不做全流程演示动画 |
| 5 | 字体 | **允许**引入 Inter + JetBrains Mono（npm 或 CSS `@font-face` / 链接），并提供系统字体回退 |

---

## 6. 验收检查（文档第十二条映射）

| 检查 | 通过标准 |
|------|----------|
| 第一眼 | 不像普通后台；像 AI 工程 / Logic 工具 |
| 第二眼 | 能立刻看出当前 Flow、Agent/Job、执行状态、选中节点 |
| 第三眼 | 执行中有克制动态，感觉系统在运行 |
| 主题 | Dark / Light 可切换且结构一致 |
| 功能 | 登录、项目 CRUD、七类 AI 创建/轮询/结果、仓库选择器仍可用 |
| 风格禁区 | 无大面积紫渐变 / 霓虹 / 玻璃拟态堆砌 |

---

`design.md` / `tasks.md` 已按上述决策生成。  
按约定：**仅在你明确回复「开始执行」后才会修改代码。**
