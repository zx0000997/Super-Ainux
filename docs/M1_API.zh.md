# M1 API 说明（任务机 + 审计骨架 + 空壳双脑）

**版本**: 0.1（对齐规格书 M1，不含真实 LLM、不含 M3 执行器沙箱）

## 目标

| 交付物 | 实现要点 |
|--------|----------|
| 任务表 + 状态机 API | `tasks` 表；`POST /v1/tasks`、`GET` 列表/详情、`POST .../transition` 校验合法边 |
| Plan / 审定包占位 | `plan_artifacts` 表；Operator 与 Supervisor **各一档** JSON + **body_hash**；任务上 `approved_plan_hash` |
| Audit 骨架 | `audit_events` **仅追加**；`prev_hash` / `row_hash` 哈希链；事件类型含创建、迁移、plan 提交 |
| 空壳适配层 | `sas_m1/adapters/*_stub.py` 生成确定性结构，**不调外部模型 API** |

约束：**Operator 进程不直接写 Audit** —— 由本 API 服务在收到 stub 结果后统一落账（符合规格 §5.5）。

## 任务状态（FSM）

参考状态（规格 §5.2）及阻塞态（§8）：

`New` → `Planning` → `PendingReview` → `Approved` → `Executing` → `Verifying` → `Completed` → `Delivered`

另有终端/旁路：`Failed`；`BlockedPayment` / `BlockedCredential` 与回到 `Executing` / `Planning` 等边已在服务内配置，供 M4 联调。

非法迁移返回 **409**。

## HTTP 端点摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 存活探针 |
| POST | `/v1/tasks` | 创建任务（`New`） |
| GET | `/v1/tasks` | 列表，`?state=&limit=&offset=` |
| GET | `/v1/tasks/{task_id}` | 详情 |
| POST | `/v1/tasks/{task_id}/transition` | 状态迁移，`actor` 填 `user` / `system` / `operator_agent` / `supervisor_agent` / `policy` |
| POST | `/v1/tasks/{task_id}/actions/submit-operator-plan-stub` | 仅 `Planning`；写 operator plan 工件；→ `PendingReview` |
| POST | `/v1/tasks/{task_id}/actions/submit-supervisor-approval-stub` | 仅 `PendingReview`；写 approved 包占位；→ `Approved`；更新 `approved_plan_hash` |
| GET | `/v1/tasks/{task_id}/plans` | 该任务下工件列表（按 `version`） |
| GET | `/v1/audit` | 审计列表，`?task_id=&limit=&offset=` |

OpenAPI 交互式文档：服务启动后访问 `/docs`。

## 配置

| 环境变量 | 含义 | 默认 |
|----------|------|------|
| `SAS_M1_DATABASE_URL` | SQLAlchemy URL | `sqlite:///./sas_m1.db` |
| `SAS_M1_GENESIS_AUDIT_HASH` | 哈希链创世前值 | 64 个 `0` |

容器部署见 [`m1/deploy/compose.yaml`](../m1/deploy/compose.yaml)（数据卷 `/data`，本机映射端口 **18081**）。

## 与 M0 / 后续里程碑

- **M0**：主机、防火墙、密钥分仓；M1 服务可部署在同一节点，建议仅绑定 `127.0.0.1:18081` 或经反向代理暴露。
- **M3**：审定包与执行器绑定、监管授权令牌；将替换 stub 路径与哈希语义。
- **M4+**：看板、通知、阻塞态产品与额度 MVP。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-03-30 | 首版 M1 实现说明 |
