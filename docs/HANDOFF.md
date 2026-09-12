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
| M3 | 能力匹配（技能50/经验30/学历20）+ 差距识别 + LLM 学习计划 + 任务状态 | ✅ 已合入 main（PR #7） |
| M4 | 简历优化四维度建议（关键词/量化/增强/结构，注入差距上下文） | ✅ 已合入 main（PR #7） |
| 管理员 | 权限校验 + /admin/users、/admin/system 接口 + 三个管理页真实数据 | ✅ 已合入 main（PR #7） |
| M5 | 面试题生成（技术/项目/行为三类）+ 多轮模拟面试 + 逐轮三维度评估 + 总评报告 | ✅ 已合入 main |
| 管理员优化 | 岗位/RAG 知识 AI 采集（真实爬取国家大学生就业服务平台，失败降级 LLM 模拟）+ 共享岗位全平台可见 + 用户删除（级联+最后管理员保护）与信息修改（用户名/邮箱/密码/角色） | ✅ 开发完成（feature-admin-optimize 分支），待推送 + 开 PR |

- **需求只到 M5（五大模块），无 M6 规格**；M1~M5 全部开发完成，管理员优化为额外增强
- **分支**：`feature-admin-optimize`（从 main 切出）；main 已含 M5 全部内容
- 管理员优化关键文件：backend `app/services/job_collector.py`（ncss 爬取 + LLM 降级）、`app/services/knowledge_collector.py`、`app/services/admin_ops.py`（级联删除）、`app/api/v1/admin.py`（采集/用户管理/岗位管理接口）、`app/models/job.py`（新增 `is_shared` 共享岗位字段）、`test_admin_collect.py`（E2E）；frontend `api/admin.ts`、`AdminJobs.vue`/`AdminRAG.vue`（AI 采集 UI）、`AdminSettings.vue`（用户编辑弹窗 + 删除）
- 岗位共享机制：管理员采集的岗位 `is_shared=True`，普通用户 GET /jobs 用 `or_(user_id==me, is_shared==True)` 可见；`job_analysis` 表是加列非新建，无历史表结构冲突
- 关键新文件（M5）：backend `app/services/interview.py`、`app/tools/interview_helper.py`（generate_interview_q 工具）、`app/api/v1/interview.py`、`test_interview_api.py`；frontend `api/interview.ts`、`views/InterviewView.vue`（由演示动画改造为真实流程）
- M3/4 关键文件：backend `app/services/matching.py`、`app/services/optimization.py`、`app/api/v1/optimize.py`、`app/api/v1/admin.py`；frontend `PlanView.vue`、`OptimizeView.vue`、`MatchDetailView.vue`、`api/knowledge.ts`、`api/admin.ts`
- 数据库注意：`interview_session` 在文档字段外补了 `resume_id`、`summary`，`interview_qa` 补了 `category`、`feedback_json`（三维度评分明细）；`learning_task` 有 `priority`、`estimated_days`（均曾删空表重建）；`Base.metadata.create_all` **不会**修改已存在的表结构，模型变更需手动 DROP 空表后重启。当前库 17 张表（12 核心 + conversation/message/knowledge_document/document_chunk + recommendation）

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
| POST /api/v1/interview/questions | 仅生成面试题（job_id + 题量 3-9，三类均匀，约 10-30s） |
| POST /api/v1/interview/session | 建面试会话并生成题库（返回 qas） |
| GET /api/v1/interview/sessions、GET /interview/session/{id} | 面试历史列表 / 详情（含问答与评估） |
| POST /api/v1/interview/session/{id}/answer | body {qa_id, answer}：LLM 三维度评估，返回本轮评估 + next_qa |
| POST /api/v1/interview/session/{id}/finish | 结束面试，LLM 汇总总评写入 session.summary |
| POST /api/v1/admin/jobs/ai-collect | AI 采集岗位 {keyword, count 1-10}：真实爬取 ncss，失败降级 LLM 模拟；入库即 is_shared 全平台可见（约 15-60s） |
| POST /api/v1/admin/knowledge/ai-collect | AI 采集知识文档 {topic, doc_count 1-3}：LLM 生成并走 RAG 切片+向量化入库 |
| GET /api/v1/admin/jobs、DELETE /admin/jobs/{id} | 全平台岗位列表（含来源/归属）/ 删除岗位及关联数据 |
| PATCH /api/v1/admin/users/{id} | 修改用户信息（username/email/role/password 全可选，仅提交字段生效） |
| DELETE /api/v1/admin/users/{id} | 删除用户及全部业务数据（级联：岗位/报告/计划/面试/对话/简历/技能/经历）；最后一名管理员受保护不可删不可降级 |

M5 设计要点：面试多轮上下文从 `interview_qa` 表加载（Memory）；LLM 出题/评估/总评均有兜底（兜底题库、中性评分、规则总评），任何 LLM 失败不阻塞流程；评估明细 JSON 结构 `{scores:{logic,completeness,professionalism}, overall, strengths, weaknesses, suggestions, source}`；E2E 脚本 `backend/test_interview_api.py`。

## 6. 下一步建议

1. 推送 `feature-admin-optimize` 并开 PR → 合并到 main（已本地验证 vue-tsc 0 错误 + E2E/浏览器全流程）
2. 课程交付项收尾（需求 11/13）：12 张核心表 ER 图（表已齐）、Docker Compose 一键部署（frontend/backend/postgres/redis/agent-service）、测试材料整理（业务/RAG/Agent + test_interview_api.py + test_admin_collect.py）
3. 新会话开工提示词模板：

```
请先阅读 D:\CareerAI\docs\HANDOFF.md（交接文档）和 docs\ 目录下的需求文档，
再执行 git log --oneline -10 与 git branch 确认当前进度，然后继续开发 <下一阶段/功能>。
```
