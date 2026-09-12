"""岗位采集去重逻辑单元测试（纯 mock，不连数据库、不访问外网）。

覆盖：
- _find_existing_shared_job：命中返回 id / 未命中返回 None / 空 title 短路不查询
- collect_jobs_from_web：正常入库 / 批内重复去重 / 库中重复跳过 /
  全部重复不提交 / count 上限截断 / 空标题忽略 / 抓取为空降级且不提交

运行（backend/ 目录）：
    .\\venv\\Scripts\\python.exe -m pytest test_job_collector_dedup.py -v
"""
import asyncio
from types import SimpleNamespace

from app.services import job_collector

ADMIN_ID = 99


# ---------- 工具 ----------

def _item(name, company, city="北京"):
    """构造 ncss 风格的岗位原始条目。"""
    return {"jobName": name, "recName": company, "areaCodeName": city}


def _job(job_id, name, company, city="北京"):
    """构造 _parse_and_save 返回的 JobAnalysis 替身。"""
    return SimpleNamespace(
        id=job_id,
        parsed_json={"position_title": name, "company": company, "city": city},
    )


def _mock_db():
    db = SimpleNamespace()
    db.commit_calls = 0

    async def commit():
        db.commit_calls += 1

    db.commit = commit
    return db


def _patch(monkeypatch, items, existing=None, jobs=None):
    """替换采集依赖：items=爬取结果, existing={(岗位名,单位): 已存在id}, jobs=新入库岗位映射。"""
    existing = existing or {}
    jobs = jobs or {}
    find_calls, save_calls = [], []

    async def fake_fetch(keyword, count):
        return items

    async def fake_fallback(keyword, count):
        return []

    async def fake_find(db, title, company):
        find_calls.append((title, company))
        return existing.get((title, company))

    async def fake_save(db, admin_user_id, jd_text, item, source):
        save_calls.append(item)
        return jobs.get((item["jobName"], item["recName"]))

    monkeypatch.setattr(job_collector, "_fetch_from_ncss", fake_fetch)
    monkeypatch.setattr(job_collector, "_llm_fallback_jobs", fake_fallback)
    monkeypatch.setattr(job_collector, "_find_existing_shared_job", fake_find)
    monkeypatch.setattr(job_collector, "_parse_and_save", fake_save)
    return find_calls, save_calls


def _run(coro):
    return asyncio.run(coro)


# ---------- _find_existing_shared_job ----------

def test_find_existing_returns_id_on_hit():
    """库中已有同（岗位名, 单位）的共享岗位 → 返回其 id。"""
    db = SimpleNamespace()

    class _Result:
        def first(self):
            return 25

    async def scalars(stmt):
        return _Result()

    db.scalars = scalars
    got = _run(job_collector._find_existing_shared_job(db, "Python 开发工程师", "智睿投研"))
    assert got == 25


def test_find_existing_returns_none_when_absent():
    """库中无匹配 → 返回 None。"""
    db = SimpleNamespace()

    class _Result:
        def first(self):
            return None

    async def scalars(stmt):
        return _Result()

    db.scalars = scalars
    got = _run(job_collector._find_existing_shared_job(db, "不存在的岗位", "某公司"))
    assert got is None


def test_find_existing_empty_title_short_circuits():
    """空 title 直接返回 None，不发起数据库查询。"""
    called = []

    async def scalars(stmt):
        called.append(stmt)
        raise AssertionError("不应执行查询")

    db = SimpleNamespace(scalars=scalars)
    got = _run(job_collector._find_existing_shared_job(db, "", "某公司"))
    assert got is None
    assert called == []


# ---------- collect_jobs_from_web ----------

def test_collect_saves_new_jobs_and_commits(monkeypatch):
    """全新岗位正常入库并提交事务。"""
    items = [_item("Python 开发工程师", "甲公司"), _item("前端工程师", "乙公司")]
    jobs = {
        ("Python 开发工程师", "甲公司"): _job(1, "Python 开发工程师", "甲公司"),
        ("前端工程师", "乙公司"): _job(2, "前端工程师", "乙公司", "上海"),
    }
    find_calls, save_calls = _patch(monkeypatch, items, jobs=jobs)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 3))

    assert result["collected_count"] == 2
    assert [c["id"] for c in result["collected"]] == [1, 2]
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0
    assert len(find_calls) == 2  # 每条都查过库
    assert len(save_calls) == 2
    assert db.commit_calls == 1  # 有入库 → 提交一次


def test_collect_batch_internal_duplicate(monkeypatch):
    """同批次出现两条相同（岗位名, 单位）→ 只入库一条，重复条计入 skipped 并关联首条 id。"""
    items = [
        _item("Python 开发工程师", "甲公司"),
        _item("Python 开发工程师", "甲公司"),  # 批内重复
        _item("前端工程师", "乙公司"),
    ]
    jobs = {
        ("Python 开发工程师", "甲公司"): _job(1, "Python 开发工程师", "甲公司"),
        ("前端工程师", "乙公司"): _job(2, "前端工程师", "乙公司"),
    }
    _, save_calls = _patch(monkeypatch, items, jobs=jobs)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 5))

    assert result["collected_count"] == 2
    assert result["skipped_count"] == 1
    assert result["skipped"][0]["existing_id"] == 1  # 关联到批内首次入库的岗位
    assert result["skipped"][0]["position_title"] == "Python 开发工程师"
    assert len(save_calls) == 2  # 重复条不再解析入库
    assert db.commit_calls == 1


def test_collect_db_duplicate_skipped_without_saving(monkeypatch):
    """库中已有同（岗位名, 单位）岗位 → 跳过且不调用解析入库。"""
    items = [_item("Python 开发工程师", "智睿投研"), _item("前端工程师", "乙公司")]
    existing = {("Python 开发工程师", "智睿投研"): 25}
    jobs = {("前端工程师", "乙公司"): _job(2, "前端工程师", "乙公司")}
    _, save_calls = _patch(monkeypatch, items, existing=existing, jobs=jobs)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 5))

    assert result["collected_count"] == 1
    assert result["collected"][0]["id"] == 2
    assert result["skipped_count"] == 1
    assert result["skipped"][0] == {
        "existing_id": 25,
        "position_title": "Python 开发工程师",
        "company": "智睿投研",
    }
    assert len(save_calls) == 1  # 重复岗位未解析入库
    assert db.commit_calls == 1


def test_collect_all_duplicates_no_commit(monkeypatch):
    """全部命中库中已有岗位 → 0 入库，且不提交事务。"""
    items = [_item("岗位A", "公司A"), _item("岗位B", "公司B")]
    existing = {("岗位A", "公司A"): 25, ("岗位B", "公司B"): 26}
    _, save_calls = _patch(monkeypatch, items, existing=existing)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 3))

    assert result["collected_count"] == 0
    assert result["skipped_count"] == 2
    assert len(save_calls) == 0
    assert db.commit_calls == 0  # 没有新增 → 不提交


def test_collect_respects_count_limit(monkeypatch):
    """count 上限：攒够即停，多余条目不处理。"""
    items = [
        _item("岗位A", "公司A"),
        _item("岗位B", "公司B"),
        _item("岗位C", "公司C"),
        _item("岗位D", "公司D"),
    ]
    jobs = {
        ("岗位A", "公司A"): _job(1, "岗位A", "公司A"),
        ("岗位B", "公司B"): _job(2, "岗位B", "公司B"),
    }
    _, save_calls = _patch(monkeypatch, items, jobs=jobs)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 2))

    assert result["collected_count"] == 2
    assert [c["id"] for c in result["collected"]] == [1, 2]
    assert len(save_calls) == 2  # 攒够 count 后停止，C/D 未解析


def test_collect_ignores_empty_title(monkeypatch):
    """无岗位名的条目直接忽略，不查库不入库。"""
    items = [_item("", "无名公司"), _item("正常岗位", "公司B")]
    jobs = {("正常岗位", "公司B"): _job(2, "正常岗位", "公司B")}
    find_calls, save_calls = _patch(monkeypatch, items, jobs=jobs)
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 5))

    assert result["collected_count"] == 1
    assert result["skipped_count"] == 0
    assert len(find_calls) == 1  # 只有正常岗位触发查重
    assert len(save_calls) == 1


def test_collect_empty_fetch_no_commit(monkeypatch):
    """爬取与 LLM 降级都为空 → 无入库、无提交、不报错。"""
    _, save_calls = _patch(monkeypatch, items=[])
    db = _mock_db()

    result = _run(job_collector.collect_jobs_from_web(db, ADMIN_ID, "Python", 3))

    assert result["collected_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0
    assert len(save_calls) == 0
    assert db.commit_calls == 0
