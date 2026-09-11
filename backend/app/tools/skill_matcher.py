"""skill_matcher Tool：计算用户技能与岗位要求的匹配度（规则计算，无需 DB）。

匹配逻辑：
- 技能匹配：用户技能与岗位必备/加分要求做模糊匹配（含大小写、常见别名），按要求级别与熟练度加权评分
- 经验匹配：用户经历年限 vs 岗位要求年限
- 输出总分（0-100）、分项得分与差距明细
"""

import re

from langchain_core.tools import tool

# 常见技能别名归一化（小写匹配）
_SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "vue.js": "vue",
    "vuejs": "vue",
    "react.js": "react",
    "reactjs": "react",
    "py": "python",
    "postgres": "postgresql",
    "psql": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "dl": "deep learning",
    "llm": "large language model",
}


def _normalize(name: str) -> str:
    name = str(name).strip().lower()
    return _SKILL_ALIASES.get(name, name)


def _flat_text(value) -> str:
    """LLM 解析出的字段可能是 str / list / dict，统一转成可搜索文本。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flat_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_flat_text(v) for v in value.values())
    return str(value)


def _extract_years(text: str) -> int | None:
    """从文本中提取经验年限要求，如 '3年以上' / '3-5年' → 3。"""
    m = re.search(r"(\d+)\s*[-~至到]?\s*\d*\s*年", text or "")
    return int(m.group(1)) if m else None


def _user_years(experiences: list[dict]) -> float:
    """根据经历列表估算用户总工作年限（按 date_range 解析，缺省按经历条数估）。"""
    total = 0.0
    pattern = re.compile(r"(\d{4})\s*[-–~至到]\s*(\d{4}|至今|现在|present)", re.I)
    for exp in experiences:
        rng = exp.get("date_range") or ""
        m = pattern.search(rng)
        if m:
            start = int(m.group(1))
            end_raw = m.group(2).lower()
            end = 2026 if any(k in end_raw for k in ("至今", "现在", "present")) else int(end_raw)
            if end > start:
                total += end - start
    if total == 0 and experiences:
        # 无法解析日期时按经历条数粗估
        work_count = sum(1 for e in experiences if e.get("type") == "work")
        total = work_count * 1.5
    return round(total, 1)


def match_skills_impl(resume_data: dict, job_data: dict) -> dict:
    """核心匹配计算：输入 resume_reader / job_analyzer 的输出，返回匹配结果。"""
    if not resume_data.get("found") or not job_data.get("found"):
        return {"matched": False, "message": "简历或岗位数据缺失，无法计算匹配度"}

    user_skills = {_normalize(s["skill_name"]): s.get("proficiency", 3) for s in resume_data.get("skills", [])}
    requirements = job_data.get("requirements", [])
    must_reqs = [r for r in requirements if r.get("requirement_level") != "plus"]
    plus_reqs = [r for r in requirements if r.get("requirement_level") == "plus"]

    gaps: list[dict] = []

    # --- 技能匹配 ---
    must_scores: list[float] = []
    for req in must_reqs:
        key = _normalize(req["skill_name"])
        level = user_skills.get(key)
        if level is None:
            # 再做包含匹配（如 "fastapi" 匹配 "fastapi framework"）
            level = next(
                (v for k, v in user_skills.items() if key in k or k in key), None
            )
        if level is None:
            must_scores.append(0.0)
            gaps.append(
                {
                    "gap_type": "skill",
                    "skill_name": req["skill_name"],
                    "priority": "high",
                    "current_level": None,
                    "target_level": 4,
                    "suggested_action": f"系统学习「{req['skill_name']}」并补充相关项目经历",
                }
            )
        else:
            # 熟练度 1-5 → 百分比；必备技能要求至少熟练(4)
            score = min(level / 4.0, 1.0) * 100
            must_scores.append(score)
            if level < 4:
                gaps.append(
                    {
                        "gap_type": "skill",
                        "skill_name": req["skill_name"],
                        "priority": "medium",
                        "current_level": level,
                        "target_level": 4,
                        "suggested_action": f"提升「{req['skill_name']}」熟练度（当前 {level}/5）",
                    }
                )

    plus_scores: list[float] = []
    for req in plus_reqs:
        key = _normalize(req["skill_name"])
        level = user_skills.get(key)
        score = 100.0 if level else 0.0
        plus_scores.append(score)
        if not level:
            gaps.append(
                {
                    "gap_type": "skill",
                    "skill_name": req["skill_name"],
                    "priority": "low",
                    "current_level": None,
                    "target_level": 3,
                    "suggested_action": f"加分项「{req['skill_name']}」可作为差异化优势学习",
                }
            )

    skill_match = 0.0
    if must_reqs or plus_reqs:
        must_avg = sum(must_scores) / len(must_scores) if must_scores else 100.0
        plus_avg = sum(plus_scores) / len(plus_scores) if plus_scores else 100.0
        # 必备技能权重 0.8，加分项权重 0.2
        skill_match = must_avg * 0.8 + plus_avg * 0.2

    # --- 经验匹配 ---
    jd_text = _flat_text(job_data.get("experience_requirement"))
    required_years = _extract_years(jd_text)
    user_years = _user_years(resume_data.get("experiences", []))
    if required_years:
        experience_match = min(user_years / required_years, 1.0) * 100
        if user_years < required_years:
            gaps.append(
                {
                    "gap_type": "experience",
                    "skill_name": "工作经验",
                    "priority": "medium",
                    "current_years": user_years,
                    "target_years": required_years,
                    "suggested_action": f"积累项目经验或突出可迁移能力（岗位要求约 {required_years} 年）",
                }
            )
    else:
        experience_match = 75.0  # 岗位未明确年限要求时给中性分

    # --- 学历匹配 ---
    user_edu = _flat_text((resume_data.get("parsed_json") or {}).get("education"))
    job_edu = _flat_text(job_data.get("education"))
    edu_rank = {"大专": 1, "本科": 2, "学士": 2, "硕士": 3, "研究生": 3, "博士": 4}

    def _rank(text: str) -> int:
        for name, r in edu_rank.items():
            if name in (text or "").lower():
                return r
        return 0

    user_rank, job_rank = _rank(user_edu), _rank(job_edu)
    if job_rank == 0:
        education_match = 80.0
    elif user_rank >= job_rank:
        education_match = 100.0
    elif user_rank > 0:
        education_match = 50.0
        gaps.append(
            {
                "gap_type": "education",
                "skill_name": "学历",
                "priority": "low",
                "suggested_action": "岗位有明确学历要求，可通过作品集与项目经验弥补",
            }
        )
    else:
        education_match = 60.0

    # --- 总分加权 ---
    overall = skill_match * 0.5 + experience_match * 0.3 + education_match * 0.2

    return {
        "matched": True,
        "overall_score": round(overall),
        "skill_match": round(skill_match),
        "experience_match": round(experience_match),
        "education_match": round(education_match),
        "user_years": user_years,
        "required_years": required_years,
        "gaps": gaps,
        "summary": (
            f"综合匹配度 {round(overall)} 分：技能 {round(skill_match)}、"
            f"经验 {round(experience_match)}、学历 {round(education_match)}；"
            f"共识别 {len(gaps)} 项差距。"
        ),
    }


@tool
def skill_matcher(resume_data: dict, job_data: dict) -> dict:
    """计算用户简历与目标岗位的匹配度，返回总分、技能/经验/学历分项与差距明细。"""
    return match_skills_impl(resume_data, job_data)
