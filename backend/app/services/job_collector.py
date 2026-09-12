"""AI 岗位采集服务：从招聘网站真实爬取 → LLM 解析 → 共享岗位入库。

真实数据源：国家大学生就业服务平台（newjob.ncss.cn，教育部官方）
- 先 GET 职位列表页建立会话 cookie（SESSION/XSRF）
- 再 GET /student/jobs/jobslist/ajax/?jobName=<关键词>&jobType=03&offset=1&limit=<N>
  返回结构化 JSON：jobName / recName（单位）/ areaCodeName（城市）/ degreeName /
  major（专业）/ headCount（招聘人数）/ lowMonthPay-highMonthPay

降级策略：爬取结果为空（站点异常/无匹配）时调用 LLM 生成模拟岗位，
source=ai_fallback，保证功能始终可用、可演示。
"""

import json
import logging
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JobAnalysis, JobRequirement
from app.services.parsing import parse_jd

logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_INDEX_URL = "https://newjob.ncss.cn/student/jobs/index.html"
_LIST_URL = "https://newjob.ncss.cn/student/jobs/jobslist/ajax/"
_PLATFORM_LABEL = "国家大学生就业服务平台"
_TIMEOUT = httpx.Timeout(15.0, read=20.0)


async def _fetch_from_ncss(keyword: str, count: int) -> list[dict]:
    """真实爬取：返回 ncss 岗位原始条目列表。"""
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": _UA, "Accept-Language": "zh-CN,zh;q=0.9"},
    ) as client:
        # 第一步：访问列表页拿会话 cookie
        await client.get(_INDEX_URL)
        # 第二步：调用职位列表 AJAX 接口
        resp = await client.get(
            _LIST_URL,
            params={"jobName": keyword, "jobType": "03", "offset": "1", "limit": str(count * 2)},
            headers={"Referer": _INDEX_URL, "X-Requested-With": "XMLHttpRequest"},
        )
        resp.raise_for_status()
        payload = resp.json()

    if not payload.get("flag"):
        return []
    data = payload.get("data") or {}
    items = data.get("list") or []
    return items[: count * 2] if isinstance(items, list) else []


def _pay_text(low, high) -> str:
    try:
        low, high = float(low or 0), float(high or 0)
    except (TypeError, ValueError):
        return "面议"
    if low <= 0 and high <= 0:
        return "面议"
    if low > 0 and high > 0:
        return f"{low:g}-{high:g} 元/月"
    return f"{max(low, high):g} 元/月"


def _build_jd_text(item: dict) -> str:
    """把爬取到的结构化字段组装成 JD 文本（供 LLM 解析与存档）。"""
    head = item.get("headCount")
    lines = [
        f"岗位名称：{item.get('jobName') or '未命名岗位'}",
        f"招聘单位：{item.get('recName') or '未公开'}",
        f"工作地点：{item.get('areaCodeName') or '不限'}",
        f"学历要求：{item.get('degreeName') or '不限'}",
        f"专业要求：{item.get('major') or '不限'}",
        f"招聘人数：{head if head else '若干'}人",
        f"月薪范围：{_pay_text(item.get('lowMonthPay'), item.get('highMonthPay'))}",
        f"信息来源：{_PLATFORM_LABEL}",
    ]
    if item.get("recTags"):
        lines.append(f"岗位标签：{item['recTags']}")
    return "\n".join(lines)


async def _parse_and_save(
    db: AsyncSession, admin_user_id: int, jd_text: str, item: dict | None, source: str
) -> JobAnalysis | None:
    """单条岗位：LLM 解析 JD → 存共享岗位。解析失败时用列表字段兜底。"""
    parsed_data: dict | None = None
    try:
        parsed = await parse_jd(jd_text)
        parsed_data = parsed.model_dump()
    except Exception:
        logger.warning("采集岗位 LLM 解析失败，使用列表字段兜底：%s", jd_text[:60])

    if parsed_data is None:
        fallback_item = item or {}
        parsed_data = {
            "position_title": fallback_item.get("jobName") or "未命名岗位",
            "education_requirement": fallback_item.get("degreeName") or None,
            "experience_requirement": None,
            "required_skills": [],
            "requirements_summary": jd_text,
        }

    parsed_data["source"] = source
    parsed_data["source_platform"] = _PLATFORM_LABEL
    if item:
        parsed_data["company"] = item.get("recName")
        parsed_data["city"] = item.get("areaCodeName")

    job = JobAnalysis(
        user_id=admin_user_id,
        jd_text=jd_text,
        parsed_json=parsed_data,
        is_shared=True,
    )
    db.add(job)
    await db.flush()

    for skill in parsed_data.get("required_skills") or []:
        if isinstance(skill, dict) and skill.get("skill_name"):
            db.add(
                JobRequirement(
                    job_id=job.id,
                    skill_name=str(skill["skill_name"])[:128],
                    requirement_level=str(skill.get("requirement_level") or "熟悉")[:32],
                    category=(skill.get("category") or None),
                )
            )
    return job


async def _llm_fallback_jobs(keyword: str, count: int) -> list[dict]:
    """爬取失败时调用 LLM 生成模拟岗位条目（与爬取条目同结构）。"""
    from langchain_core.messages import HumanMessage, SystemMessage

    from app.llm.client import get_chat_llm

    try:
        llm = get_chat_llm()
        resp = await llm.ainvoke(
            [
                SystemMessage(
                    "你是招聘数据生成器。模拟招聘网站上真实的岗位发布信息，输出 JSON："
                    '{"jobs": [{"jobName": "...", "recName": "公司名", "areaCodeName": "城市", '
                    '"degreeName": "学历要求", "major": "专业", "headCount": 1, '
                    '"lowMonthPay": 0, "highMonthPay": 0, "recTags": "职责与任职要求概述（100字内）"}]}。'
                    "岗位信息要贴近真实市场，公司名要真实合理。仅输出 JSON。"
                ),
                HumanMessage(f"生成 {count} 条与「{keyword}」相关的在招岗位。"),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
        start, end = text.find("{"), text.rfind("}")
        raw = json.loads(text[start : end + 1])
        return [j for j in raw.get("jobs", []) if isinstance(j, dict)][:count]
    except Exception:
        logger.exception("LLM 生成模拟岗位失败")
        return []


async def collect_jobs_from_web(
    db: AsyncSession, admin_user_id: int, keyword: str, count: int
) -> dict:
    """管理员采集入口：真实爬取 ncss → 解析入库；失败降级 LLM 模拟。"""
    source, source_label = "web_ncss", f"实时采集（{_PLATFORM_LABEL}）"
    items: list[dict] = []
    try:
        items = await _fetch_from_ncss(keyword, count)
    except Exception:
        logger.exception("ncss 爬取失败，降级为 LLM 模拟岗位")

    if not items:
        source, source_label = "ai_fallback", "AI 模拟（真实站点暂无数据）"
        items = await _llm_fallback_jobs(keyword, count)
        item_ctx = None
    else:
        item_ctx = None

    collected, failed = [], 0
    for item in items[:count]:
        try:
            job = await _parse_and_save(db, admin_user_id, _build_jd_text(item), item, source)
            if job is None:
                failed += 1
                continue
            collected.append(
                {
                    "id": job.id,
                    "position_title": (job.parsed_json or {}).get("position_title"),
                    "company": (job.parsed_json or {}).get("company"),
                    "city": (job.parsed_json or {}).get("city"),
                }
            )
        except Exception:
            failed += 1
            logger.exception("采集岗位入库失败")

    if collected:
        await db.commit()

    return {
        "source": source,
        "source_label": source_label,
        "keyword": keyword,
        "collected": collected,
        "collected_count": len(collected),
        "failed_count": failed,
    }
