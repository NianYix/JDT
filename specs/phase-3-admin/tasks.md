# AI Engineering Copilot — Phase 3 Tasks（SQLAdmin 管理端）

> 状态：已执行完成  
> 验收：pytest **10 passed**；`/admin` 已挂载

## 勾选

- [x] T1 配置与依赖（sqladmin + itsdangerous）
- [x] T2 Admin 模块（auth / views / setup_admin）
- [x] T3 接入 `create_app`
- [x] T4 测试与 README

## 使用

1. 重启 Backend（或重新运行 `start.bat`）
2. 打开 http://localhost:8000/admin
3. 登录：`admin` / `admin123456`（以 `.env` 为准）
4. 管理 Users / Projects 增删改查
