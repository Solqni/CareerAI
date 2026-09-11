"""知识库接口补充测试：列表 / 详情 / 检索 / 问答 / 删除。"""
import json
import urllib.request

BASE = "http://localhost:8000/api/v1"


def call(method, path, body=None, token=None, timeout=120):
    req = urllib.request.Request(BASE + path, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw[:300]}


status, res = call("POST", "/auth/login", {"username": "agenttest", "password": "agent1234"})
token = res.get("access_token")

status, res = call("GET", "/knowledge/", token=token)
print("列表:", status, json.dumps(res, ensure_ascii=False)[:300])

status, res = call("GET", "/knowledge/5", token=token)
print("详情:", status, json.dumps(res, ensure_ascii=False)[:200])

status, res = call("POST", "/knowledge/search", {"query": "如何学习 FastAPI", "top_k": 3}, token=token)
print("检索:", status, json.dumps(res, ensure_ascii=False)[:400])

status, res = call("POST", "/knowledge/ask", {"question": "RAG 学习应该分几个阶段？"}, token=token, timeout=180)
print("问答:", status, json.dumps(res, ensure_ascii=False)[:400])

status, res = call("DELETE", "/knowledge/4", token=token)
print("删除:", status, json.dumps(res, ensure_ascii=False)[:200])
