"""阶段二端到端测试：登录 → 简历解析 → JD解析 → 知识库上传 → Agent 工作流 → Agent 对话。"""
import base64
import json
import urllib.request

BASE = "http://localhost:8000/api/v1"
TOKEN = None


def call(method: str, path: str, body=None, raw_body: bytes | None = None,
         headers: dict | None = None, timeout: int = 180):
    req = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if body is not None and "Content-Type" not in (headers or {}):
        req.add_header("Content-Type", "application/json")
    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw[:500]}


# ---------- 1. 登录 ----------
status, res = call("POST", "/auth/login", {"username": "agenttest", "password": "agent1234"})
TOKEN = res.get("access_token") or (res.get("data") or {}).get("access_token")
assert TOKEN, f"登录失败: {res}"


def _user_id_from_token(token: str) -> int:
    """从 JWT payload 的 sub 字段解析 user_id。"""
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return int(json.loads(base64.urlsafe_b64decode(payload_b64))["sub"])


user_id = _user_id_from_token(TOKEN)
print("1. 登录 OK, user_id =", user_id)

# ---------- 2. 简历解析 ----------
resume_text = """张伟，男，2024年6月毕业于华中科技大学计算机科学与技术专业，本科。
技能：Python 熟练，FastAPI 了解，MySQL 熟练，Docker 一般，了解 Redis，会用 Git。
实习经历：2023.07-2023.12 在字节跳动后端开发实习，参与内容推荐服务的接口开发与优化，
使用 Python + FastAPI 开发了 10+ 个接口，将接口平均响应时间从 200ms 降低到 80ms。
项目经历：校园二手交易平台，使用 FastAPI + MySQL + Redis 实现，负责商品与订单模块。"""
status, res = call("POST", "/resume/parse", {"raw_text": resume_text})
print("2. 简历解析:", status, json.dumps(res, ensure_ascii=False)[:200])

# ---------- 3. JD 解析 ----------
jd_text = """岗位：后端开发工程师（Python）
职责：负责核心业务系统的设计与开发，参与高并发服务架构优化。
要求：
1. 本科及以上学历，计算机相关专业；
2. 精通 Python，熟悉 FastAPI / Flask 等框架；
3. 熟悉 MySQL、Redis，了解消息队列；
4. 熟悉 Docker 与 Linux 环境；
5. 有 LLM / RAG / Agent 项目经验者优先；
6. 3 年以上后端开发经验。"""
status, res = call("POST", "/jobs/parse", {"jd_text": jd_text})
print("3. JD解析:", status, json.dumps(res, ensure_ascii=False)[:200])
job_id = res.get("id") or (res.get("data") or {}).get("id")
assert job_id, f"未拿到 job_id: {res}"

# ---------- 4. 知识库上传（RAG）----------
boundary = "----testboundary123"
doc_content = """Python 后端学习路线指南

第一阶段：夯实基础（约 30 天）
深入理解 Python 核心特性：装饰器、生成器、上下文管理器与 asyncio 异步编程。
推荐资源：官方教程、《流畅的 Python》。

第二阶段：Web 框架进阶（约 45 天）
系统学习 FastAPI：依赖注入、中间件、Pydantic 数据校验、后台任务。
动手完成一个包含用户认证、CRUD、分页与过滤的完整 REST API 项目。

第三阶段：数据存储（约 30 天）
MySQL 索引原理与 SQL 优化；Redis 五大数据结构与缓存穿透/雪崩解决方案；
PostgreSQL 入门与 pgvector 向量检索。

第四阶段：AI 工程化（约 45 天）
学习 LangChain 框架、RAG 检索增强生成原理、向量数据库选型，
以及 LangGraph 多智能体编排，完成一个 AI 问答机器人项目。"""


def multipart(field, filename, content: bytes, ctype="text/markdown"):
    part = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode() + content + b"\r\n"
    return part


body = (
    multipart("file", "python-learning-roadmap.md", doc_content.encode())
    + f"--{boundary}--\r\n".encode()
)
status, res = call(
    "POST",
    "/knowledge/upload",
    raw_body=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
print("4. 知识库上传:", status, json.dumps(res, ensure_ascii=False)[:250])

# ---------- 5. Agent 完整工作流 ----------
status, res = call("POST", "/agent/run", {"user_id": user_id, "job_id": job_id}, timeout=300)
print("5. Agent/run:", status, "code =", res.get("code"))
report = (res.get("data") or {})
print("   report_id:", report.get("report_id"), "plan_id:", report.get("plan_id"))
rep = report.get("report") or {}
print("   success:", rep.get("success"), "| 总分:", rep.get("overall_score"),
      "| 技能:", rep.get("skill_match"), "| 经验:", rep.get("experience_match"),
      "| 学历:", rep.get("education_match"))
print("   analysis:", str(rep.get("analysis"))[:150])
print("   gaps:", json.dumps(rep.get("gaps"), ensure_ascii=False)[:300])
print("   plan tasks:", len(rep.get("plan") or []), json.dumps(rep.get("plan"), ensure_ascii=False)[:300])
print("   knowledge_sources:", json.dumps(rep.get("knowledge_sources"), ensure_ascii=False)[:200])
print("   errors:", rep.get("errors"))

# ---------- 6. Agent 对话 ----------
status, res = call("POST", "/agent/chat", {"message": "我的技能和目标岗位匹配吗？怎么补齐差距？"}, timeout=120)
print("6. Agent/chat:", status, "code =", res.get("code"))
chat = res.get("data") or {}
print("   conversation_id:", chat.get("conversation_id"), "tools_used:", chat.get("tools_used"))
print("   answer:", str(chat.get("answer"))[:300])
