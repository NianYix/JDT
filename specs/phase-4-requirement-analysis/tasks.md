# AI Engineering Copilot — Phase 4 Tasks（Requirement Analysis）

> 状态：已执行完成  
> 验收：pytest 全绿；Frontend build 通过

## 勾选

- [x] T1 配置与 openai 依赖
- [x] T2 Model / Alembic / Repository / Schemas
- [x] T3 LLM Provider
- [x] T4 Service + API
- [x] T5 测试
- [x] T6 Frontend 项目详情页

## 使用

1. 在 `.env` 配置 `LLM_API_KEY`（及可选 `LLM_BASE_URL` / `LLM_MODEL`）
2. 重启 Backend；SQLite 用 `start.bat` 会 `init_db` 建表；Postgres 执行 `alembic upgrade head`
3. 打开项目详情 →「需求分析」提交文本
