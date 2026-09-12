"""M5 面试准备模块端到端测试（需求 12.1 业务功能测试：面试模拟）。

流程：登录 → 取岗位（无则解析一份 JD）→ 创建面试会话（3 题）→
逐轮提交答案（校验三维度评分）→ 结束生成总评 → 历史列表 / 详情校验。

运行（backend/ 目录，需后端已启动）：
    .\\venv\\Scripts\\python.exe test_interview_api.py
"""
import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1"
TOKEN = None


def call(method: str, path: str, body=None, timeout: int = 180):
    req = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    else:
        data = None
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
print("1. 登录 OK")

# ---------- 2. 准备一个已解析岗位 ----------
status, jobs = call("GET", "/jobs")
if jobs:
    job_id = jobs[0]["id"]
    print(f"2. 复用已有岗位 id={job_id}（{jobs[0].get('position_title')}）")
else:
    jd_text = """岗位：后端开发工程师（Python）
要求：1. 本科及以上，计算机相关专业；2. 精通 Python，熟悉 FastAPI；
3. 熟悉 MySQL、Redis、Docker；4. 有 RAG / Agent 项目经验者优先。"""
    status, job = call("POST", "/jobs/parse", {"jd_text": jd_text})
    job_id = job.get("id")
    assert job_id, f"JD 解析失败: {job}"
    print(f"2. 新解析岗位 id={job_id}")

# ---------- 3. 仅生成面试题 ----------
status, bank = call(
    "POST", "/interview/questions", {"job_id": job_id, "question_count": 3}
)
assert status == 200 and len(bank.get("questions", [])) == 3, f"题库生成异常: {bank}"
cats = {q["category"] for q in bank["questions"]}
print(f"3. 题库生成 OK（来源 {bank.get('source')}，题型 {cats}）")
for q in bank["questions"]:
    print("   -", q["category"], q["question"][:50])

# ---------- 4. 创建面试会话 ----------
status, session = call(
    "POST",
    "/interview/session",
    {"job_id": job_id, "question_count": 3},
)
assert status == 201 and len(session.get("qas", [])) == 3, f"创建会话异常: {session}"
session_id = session["id"]
print(f"4. 创建面试会话 OK id={session_id}，岗位：{session.get('position_title')}")

# ---------- 5. 逐轮作答 ----------
answers = {
    "technical": "我在项目中用 FastAPI 开发过 10 余个异步接口，深入理解了 asyncio "
    "事件循环与依赖注入；用 Redis 做缓存把接口 P95 延迟从 200ms 降到 80ms。",
    "project": "我负责过校园二手交易平台，用 STAR 来说：情境是订单并发超卖；任务由我设计"
    "方案；我用 Redis 分布式锁 + MySQL 乐观扣库存实现；结果大促期间零超卖。",
    "behavioral": "有一次和前端同学对接口设计产生分歧，我先听他的诉求，再用数据说明两种"
    "方案的调用次数差异，最后各取一半达成一致，项目按期上线。",
}
for i, qa in enumerate(session["qas"], 1):
    status, result = call(
        "POST",
        f"/interview/session/{session_id}/answer",
        {"qa_id": qa["id"], "answer": answers.get(qa["category"], "这是我的回答，我会结合具体项目举例说明。")},
    )
    assert status == 200, f"第 {i} 轮提交失败: {result}"
    answered = result["qa"]
    fj = answered.get("feedback_json") or {}
    scores = fj.get("scores", {})
    print(
        f"5.{i} {qa['category']} 评分完成: 总分 {answered.get('score')} "
        f"逻辑 {scores.get('logic')} / 完整 {scores.get('completeness')} / "
        f"专业 {scores.get('professionalism')}（{fj.get('source')}）"
    )
    assert answered.get("answer"), "回答未持久化"
    assert answered.get("feedback"), "评估文本缺失"
    if i < 3:
        assert result["next_qa"], "应返回下一题"
    else:
        assert result["is_finished"], "最后一题后应标记完成"

# ---------- 6. 结束面试，生成总评 ----------
status, finished = call("POST", f"/interview/session/{session_id}/finish", {})
assert status == 200 and finished.get("status") == "finished", f"结束异常: {finished}"
assert finished.get("summary"), "总评报告缺失"
print("6. 总评报告生成 OK：")
print("   " + finished["summary"][:220].replace("\n", "\n   "))

# ---------- 7. 历史列表与详情 ----------
status, items = call("GET", "/interview/sessions")
assert status == 200 and any(it["id"] == session_id for it in items), "历史列表缺失"
mine = next(it for it in items if it["id"] == session_id)
print(
    f"7. 历史列表 OK：{mine['answered_count']}/{mine['qa_count']} 轮，"
    f"平均分 {mine['average_score']}"
)

status, detail = call("GET", f"/interview/session/{session_id}")
assert status == 200 and len(detail["qas"]) == 3, "详情查询异常"
print("8. 详情查询 OK，全流程通过 ✅")
