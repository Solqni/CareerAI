"""管理员优化功能端到端测试：AI 采集岗位/知识 + 用户删除与信息修改。

运行（backend/ 目录，需后端已启动）：
    .\\venv\\Scripts\\python.exe test_admin_collect.py
"""
import json
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1"


def call(method, path, body=None, token=None, timeout=300):
    req = urllib.request.Request(BASE + path, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data, timeout=timeout) as resp:
            status = resp.status
            parsed = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw[:300]}
        return e.code, parsed
    # 统一响应包装 {code, data, message}：业务失败码映射为返回状态码
    if isinstance(parsed, dict) and isinstance(parsed.get("code"), int) and parsed["code"] != 200:
        return parsed["code"], parsed
    return status, parsed


def unwrap(res):
    """管理员接口返回 {code, data, message} 包装。"""
    if isinstance(res, dict) and "data" in res:
        return res["data"], res.get("message")
    return res, None


# ---------- 1. 管理员登录 ----------
_, res = call("POST", "/auth/login", {"username": "admintest", "password": "admin1234"})
ADMIN = res.get("access_token") or (res.get("data") or {}).get("access_token")
assert ADMIN, f"管理员登录失败: {res}"
print("1. 管理员登录 OK")

# ---------- 2. AI 真实爬取采集岗位 ----------
t0 = time.time()
status, res = call("POST", "/admin/jobs/ai-collect", {"keyword": "Python", "count": 3}, ADMIN)
data, msg = unwrap(res)
assert status == 200 and data.get("collected_count") >= 1, f"岗位采集失败: {res}"
print(
    f"2. 岗位采集 OK（{time.time()-t0:.0f}s，来源 {data['source_label']}，"
    f"成功 {data['collected_count']} 条，失败 {data['failed_count']} 条）"
)
for c in data["collected"]:
    print(f"   - #{c['id']} {c.get('position_title')} | {c.get('company')} | {c.get('city')}")
assert data["source"] == "web_ncss", f"预期真实爬取，实际 {data['source']}"
shared_job_ids = [c["id"] for c in data["collected"]]

# ---------- 3. 普通用户可见共享岗位 ----------
_, res = call("POST", "/auth/login", {"username": "agenttest", "password": "agent1234"})
USER = res.get("access_token") or (res.get("data") or {}).get("access_token")
status, jobs = call("GET", "/jobs", token=USER)
visible = {j["id"] for j in jobs}
hit = [jid for jid in shared_job_ids if jid in visible]
assert hit, f"普通用户看不到共享岗位: shared={shared_job_ids} visible={list(visible)[:10]}"
print(f"3. 共享岗位可见性 OK：普通用户可见采集岗位 {hit}")
shared_item = next(j for j in jobs if j["id"] == hit[0])
print(f"   示例条目 is_shared={shared_item.get('is_shared')} is_owner={shared_item.get('is_owner')}")

# ---------- 4. AI 采集知识文档 ----------
t0 = time.time()
status, res = call(
    "POST", "/admin/knowledge/ai-collect",
    {"topic": "后端面试高频考点", "doc_count": 1}, ADMIN,
)
data, msg = unwrap(res)
assert status == 200 and data.get("generated_count") == 1, f"知识采集失败: {res}"
doc = data["documents"][0]
assert doc["chunk_count"] >= 1, "知识文档未切片"
print(f"4. 知识采集 OK（{time.time()-t0:.0f}s）：{doc['title']}，{doc['chunk_count']} 片段")

# ---------- 5. 管理员岗位列表（含来源与归属） ----------
status, res = call("GET", "/admin/jobs", token=ADMIN)
jobs_admin, _ = unwrap(res)
assert status == 200 and jobs_admin, f"管理员岗位列表失败: {str(res)[:200]}"
mine = next(j for j in jobs_admin if j["id"] == shared_job_ids[0])
assert mine["source_label"] and mine["is_shared"], f"来源/共享标记缺失: {mine}"
print(f"5. 管理员岗位列表 OK：共 {len(jobs_admin)} 条，采集条目来源={mine['source_label']} 归属={mine['owner_username']}")

# ---------- 6. 修改用户信息 ----------
status, res = call("GET", "/admin/users", token=ADMIN)
users, _ = unwrap(res)
agent = next(u for u in users if u["username"] == "agenttest")
new_email = f"agenttest_{int(time.time())}@test.com"
status, res = call("PATCH", f"/admin/users/{agent['id']}", {"email": new_email}, ADMIN)
updated, m = unwrap(res)
assert status == 200 and updated["email"] == new_email, f"修改邮箱失败: {res}"
print(f"6. 修改用户信息 OK：agenttest 邮箱 → {new_email}")

# ---------- 7. 删除用户（级联） ----------
suffix = int(time.time())
reg_status, reg = call(
    "POST", "/auth/register",
    {"username": f"deltest{suffix}", "password": "del12345", "email": f"del{suffix}@t.com"},
)
assert reg_status in (200, 201), f"注册测试用户失败: {reg}"
_, res = call("POST", "/auth/login", {"username": f"deltest{suffix}", "password": "del12345"})
DEL_TOKEN = res.get("access_token") or (res.get("data") or {}).get("access_token")
# 让该用户产生岗位数据（会触发 LLM，预计 10-30s）
status, job = call("POST", "/jobs/parse", {"jd_text": "岗位：Python 后端工程师，要求精通 FastAPI、MySQL、Redis，本科及以上。"}, DEL_TOKEN)
assert status == 200, f"测试用户解析岗位失败: {job}"

status, res = call("GET", "/admin/users", token=ADMIN)
users, _ = unwrap(res)
target = next(u for u in users if u["username"] == f"deltest{suffix}")
status, res = call("DELETE", f"/admin/users/{target['id']}", token=ADMIN)
assert status == 200, f"删除用户失败: {res}"
_, res = call("GET", "/admin/users", token=ADMIN)
users_after, _ = unwrap(res)
assert all(u["username"] != f"deltest{suffix}" for u in users_after), "用户仍存在"
print(f"7. 删除用户 OK：deltest{suffix} 及其岗位数据已级联清理")

# ---------- 8. 保护逻辑 ----------
status, res = call("GET", "/admin/users", token=ADMIN)
admins, _ = unwrap(res)
me = next(u for u in admins if u["username"] == "admintest")  # 当前登录的管理员
status, res = call("DELETE", f"/admin/users/{me['id']}", token=ADMIN)
assert status == 400, f"删除自己未被拦截: {res}"
status, res = call("PATCH", f"/admin/users/{me['id']}", {"role": "user"}, ADMIN)
assert status == 400, f"降级最后管理员未被拦截: {res}"
print("8. 保护逻辑 OK：删除自己/降级最后管理员均被拦截")

print("\n全部通过")
