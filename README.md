# CareerAI · AI求职与职业成长智能体

> 集简历解析、岗位分析、能力匹配、学习规划、面试准备于一体的 AI 智能体平台。
> 技术路线：**Python + FastAPI + LangChain**

## 项目简介

CareerAI 面向在校大学生与应届毕业生，提供「评估 → 分析 → 规划 → 执行 → 成长」一站式求职与职业发展辅助服务。

- **M1 用户与简历**：注册登录 / 简历上传解析（PDF/Word）/ 技能管理 / 能力画像
- **M2 岗位分析**：JD 文本解析 / 岗位知识库（RAG）/ 岗位查询
- **M3 能力匹配与规划**：人岗匹配计算 / 差距分析 / 匹配报告 / 学习计划
- **M4 简历优化**：关键词优化 / 经历量化建议 / 内容增强（不编造经历）
- **M5 面试准备**：面试题生成 / 模拟面试对话 / 答案评估 / 反馈报告

## 技术栈

| 类别 | 选型 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / Pydantic |
| AI 框架 | LangChain + LangGraph |
| ORM | SQLAlchemy (async) |
| 数据库 | PostgreSQL + pgvector |
| 缓存 | Redis |
| 前端 | Vue 3 + TypeScript + Vite |
| LLM | DeepSeek API (Chat + Embedding) |
| 容器化 | Docker + Docker Compose |

## 目录结构

CareerAI/
├── backend/            # FastAPI 后端（含 Agents / Tools / RAG）
│   ├── app/
│   │   ├── api/        # 路由层 (v1)
│   │   ├── core/       # 配置 / 安全 / 数据库连接
│   │   ├── models/     # SQLAlchemy 模型
│   │   ├── schemas/    # Pydantic 数据模型
│   │   ├── services/   # 业务逻辑
│   │   ├── repositories/ # 数据访问
│   │   ├── agents/     # LangGraph Agent 编排
│   │   ├── tools/      # Tool Calling 工具集
│   │   ├── rag/        # RAG 知识库
│   │   └── llm/        # LLM 客户端封装
│   ├── tests/
│   ├── scripts/        # 初始化 SQL 等
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/           # Vue 3 前端
├── agent-service/      # Agent 独立服务（复用 backend 镜像）
├── docs/               # 需求文档
├── docker-compose.yml
├── .env.example
└── README.md

## 快速开始

### 1. 环境准备
- Docker & Docker Compose
- 一个可用的 **DeepSeek API Key**（用于 LLM 调用）

### 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等配置

### 3. 一键启动
docker compose up -d --build

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |

### 4. 本地开发
后端: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
前端: cd frontend && npm install && npm run dev

## 开发规范
- Git 分支：feature/user、feature/rag、feature/agent 等
- Commit 前缀：feat / fix / refactor / docs / test / chore
- 后端分层：router → service → repository
- LLM API Key 仅通过环境变量注入，严禁提交至代码仓库

