# CareerAI 开发交接文档（AI 会话续接用）

> 用途：更换开发账号/新开 AI 会话时，让 AI 先读本文档 + docs/ 下需求文档，即可继续开发。
> 最后更新：2026-09-12

## 1. 项目概览

- **项目**：CareerAI（AI 求职与职业成长智能体），GitHub: https://github.com/Solqni/CareerAI
- **路径**：`D:\CareerAI`（backend = FastAPI，frontend = Vue3 + Vite + Pinia）
- **技术栈**：FastAPI + SQLAlchemy(async) + LangChain/LangGraph + DeepSeek（百炼，OpenAI 兼容接口）+ PostgreSQL + pgvector + Redis（Docker 容器 careerai-postgres）
- **需求文档**：`docs/` 目录（Word/PDF），第 3 章 M1~M6 小节、第 4 节数据表、第 8 节接口/Pydantic
- **硬性约定**：API Key 只从 backend/.env 读；LLM 统一走 `app/llm/client.py` 的 `get_chat_llm()`；Pydantic v2；知识库接口是 ok()/fail() 包装（{code,data,message}），其余接口（auth/resume/job/match）是裸 JSON + HTTPException——前端 axios 直接取 data，**不要强行统一格式以免破坏前端**

## 2. 当前进度（截至本文档更新）

| 阶段 | 内容 | 状态 |
|------|------|------|
| M1 | 注册登录 + 简历上传/解析 | ✅ 已合入 main |
| M2 | 岗位 JD 解析 + RAG 知识库 + LangGraph Agent（4 tools） | ✅ 已合入 main（PR #6） |
| M3 | 能力匹配（技能50/经验30/学历20）+ 差距识别 + LLM 学习计划 + 任务状态 | ✅ 开发完成，待合并 |
| M4 | 简历优化四维度建议（关键词/量化/增强/结构，注入差距上下文） | ✅ 开发完成，待合并 |
| 管理员 | 权限校验 + /admin/users、/admin/system 接口 + 三个管理页真实数据 | ✅ 开发完成，待合并 |

- **分支**：`feature-m3-match-optimize`（领先 main 3 个提交），**PR #7 待合并**：https://github.com/Solqni/CareerAI/pull/7
- 关键新文件：backend `app/services/matching.py`、`app/services/optimization.py`、`app/api/v1/optimize.py`、`app/api/v1/admin.py`；frontend `PlanView.vue`、`OptimizeView.vue`、`MatchDetailView.vue`、`api/knowledge.ts`、`api/admin.ts`
- 数据库注意：`learning_task` 表新增了 `priority`、`estimated_days` 列（已删表重建）；`Base.metadata.create_all` **不会**修改已存在的表结构，模型变更需手动 DROP 空表后重启

## 3. 环境坑（重要，来自实际踩坑）

1. **后端不要加 `--reload`**：watchfiles 在沙箱内重启会崩掉整个服务；改代码后手动重启
2. **必须用 backend venv 的 python**：`.\venv\Scripts\python.exe`（全局 D:\python 缺 pgvector，且 passlib+bcrypt 组合会挂）
3. **Docker Desktop 会静默停止**：后端报 ConnectionRefused 时先重启 Docker，等 careerai-postgres healthy
4. pgvector 必须 >=0.4.0（0.3.x 锁 numpy 1.26.4，Python 3.13 不兼容）
5. LLM 返回的 JSON 字段类型不稳定（str/list/dict），字符串操作前先过 `app/tools/skill_matcher.py` 的 `_flat_text()`
6. `db.commit()` 会使 relationship 过期，返回 ORM 对象前需 selectinload 重新查询
7. 本会话曾出现文件编辑被环境回退的现象——每次编辑后用 grep/read 复核关键行

## 4. 启动与测试

```powershell
# 后端（backend/ 目录）
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 前端（frontend/ 目录）
npm run dev   # http://localhost:5173
```

- **测试账号**：普通 `agenttest/agent1234`（user_id 17），管理员 `admintest/admin1234`
- **Swagger**：http://127.0.0.1:8000/docs
- E2E 脚本：backend/test_agent_flow.py、test_knowledge_api.py
- CI：GitHub Actions 跑 `vue-tsc --noEmit`（本地 dev 不检查类型，提交前手动跑一遍，确保 0 错误）

## 5. 核心接口速查（阶段3）

| 接口 | 说明 |
|------|------|
| POST /api/v1/match | 简历×岗位全流程匹配（评分+差距+报告+LLM计划一次入库，约10-60s） |
| GET /api/v1/match/{id}、GET /api/v1/match/list | 报告详情 / 历史列表 |
| GET /api/v1/match/{id}/plan、PATCH /api/v1/match/plan/tasks/{task_id} | 学习计划查询 / 任务状态（todo/in_progress/done） |
| POST /api/v1/optimize | 简历优化建议（job_id 必填，resume_id 缺省取最新） |
| GET /api/v1/resume/list | 当前用户简历列表（匹配/优化下拉用） |
| POST /api/v1/admin/* | 管理员接口（403 拦非 admin） |

## 6. 下一步建议

1. 合并 PR #7 到 main（CI 已本地验证 vue-tsc 0 错误）
2. 下一阶段按需求文档继续（M5/M6，面试模拟 interview 路由已有雏形 `app/api/v1/interview.py`）
3. 新会话开工提示词模板：

```
请先阅读 D:\CareerAI\docs\HANDOFF.md（交接文档）和 docs\ 目录下的需求文档，
再执行 git log --oneline -10 与 git branch 确认当前进度，然后继续开发 <下一阶段/功能>。
```
