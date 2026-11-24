# Mori Admin API 局部入口

适用于 `api/` 目录（可选全栈底座）。先遵守根 [AGENTS.md](../AGENTS.md)，再查阅 [后端编码规范](../docs/backend.md) 与 [模块开发指南](../docs/module-development.md)。

## 本地约束

- **分层边界**：路由层（`api.py`）只处理 HTTP 协议、参数校验、权限鉴权与响应包装，严禁写 SQL；业务逻辑与数据访问收敛在 `service/`，不返回 FastAPI `Response` 或 `ApiResponse`。
- **数据访问**：原生 SQL 统一经 [session.py](app/db/session.py) 参数化执行（命名占位符 + 字典传参），不建立 ORM 实体映射；多步写入共享同一 `Session` 并传 `commit=False`，最后统一提交、异常回滚。
- **路由与鉴权**：新 `APIRouter` 须在 [main.py](app/main.py) 注册；受保护接口显式注入 `get_current_user` / `require_permission()`，管理类写操作按需声明 `operation_log()`，并校验资源归属。
- **结构与迁移**：表结构或静态权限/菜单变更同步维护 [init.sql](app/db/init.sql) 与 `app/db/migrations/` 增量迁移及 [init_db.py](app/db/init_db.py)，不修改已发布迁移。
- **安全与脱敏**：配置统一走 [config.py](app/core/config.py)；日志、审计与错误响应严禁泄露密码、Token、SQL 或异常堆栈。

## 改动前检查

- 接口契约或响应模型变更时，同步检查 `schemas.py` 与前端 `web/src/api/*.ts` 消费者。
- 新增运行依赖写入 `requirements.txt` 前，确认 [Dockerfile](Dockerfile) 可正常安装。

## 验证原则

- 遵循针对性最小充分验证：仅验证本次改动直接影响的接口行为、权限边界、异常映射，以及（涉及表结构时）空库初始化与已有库升级路径；纯文档改动无需运行业务测试。
