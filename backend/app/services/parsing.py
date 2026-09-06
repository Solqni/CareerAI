"""基于规则的简历 / JD 解析服务（不依赖 LLM，开箱可用）。

后续可将 `parse_resume` / `parse_jd` 内部替换为 LLM 实现，
保持函数签名不变即可。
"""

import re

# 常见技能词典（可按需扩充）
SKILL_DICTIONARY: list[str] = [
    # 编程语言
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Swift", "Kotlin", "R", "MATLAB", "Scala",
    # 前端
    "Vue", "React", "Angular", "HTML", "CSS", "Sass", "Less", "Webpack", "Vite", "jQuery", "Bootstrap", "Tailwind CSS", "Element Plus", "ECharts", "微信小程序",
    # 后端 / 框架
    "Django", "Flask", "FastAPI", "Spring Boot", "Spring Cloud", "MyBatis", "Node.js", "Express", "NestJS",
    # 数据库 / 中间件
    "MySQL", "PostgreSQL", "Oracle", "SQL Server", "SQLite", "MongoDB", "Redis", "Elasticsearch", "Kafka", "RabbitMQ", "SQL",
    # 运维 / 工具
    "Linux", "Docker", "Kubernetes", "Git", "Jenkins", "CI/CD", "Nginx", "AWS", "阿里云", "腾讯云", "微服务",
    # 数据 / AI
    "机器学习", "深度学习", "数据分析", "数据挖掘", "自然语言处理", "NLP", "计算机视觉", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Spark", "Hadoop", "大模型", "AIGC", "Prompt Engineering",
    # 软技能
    "团队协作", "沟通能力", "项目管理", "英语", "产品设计", "Axure", "Figma", "Photoshop", "Office", "Excel", "PPT", "文案写作", "市场调研", "用户运营",
]

EDUCATION_KEYWORDS = ["博士", "硕士", "研究生", "本科", "大专", "专科", "MBA"]

_LEVEL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(精通|专家)"), "expert"),
    (re.compile(r"(熟练|熟练掌握|熟悉)"), "proficient"),
    (re.compile(r"(掌握|了解)"), "familiar"),
    (re.compile(r"(优先|加分)"), "plus"),
]


def _extract_skills(text: str) -> list[str]:
    """从文本中匹配技能词典，返回去重后的技能列表。"""
    lowered = text.lower()
    found = []
    for skill in SKILL_DICTIONARY:
        if skill.lower() in lowered:
            found.append(skill)
    # 去重保序
    seen: set[str] = set()
    result = []
    for s in found:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def parse_resume(text: str) -> dict:
    """规则解析简历文本，提取基本信息、教育、技能、经历。"""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"1[3-9]\d{9}", text)

    education = None
    for kw in EDUCATION_KEYWORDS:
        if kw in text:
            education = "硕士" if kw == "研究生" else kw
            break

    skills = _extract_skills(text)

    # 经历：提取包含年份区间/公司/职位特征的行
    experiences = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 6:
            continue
        if re.search(r"(19|20)\d{2}", line) and re.search(
            r"(公司|有限|集团|实习|工作|项目|工程师|经理|专员|主管|实习|大学|学院)", line
        ):
            experiences.append(line[:120])
        if len(experiences) >= 8:
            break

    return {
        "name": None,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "education": education,
        "skills": skills,
        "experiences": experiences,
        "summary": f"识别到 {len(skills)} 项技能、{len(experiences)} 段经历",
    }


def parse_jd(jd_text: str) -> dict:
    """规则解析 JD，提取岗位要求并分级。"""
    requirements: list[dict] = []
    seen: set[str] = set()

    lines = [ln.strip() for ln in jd_text.splitlines() if ln.strip()]

    def add_requirement(skill: str, level: str, category: str) -> None:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            requirements.append(
                {"skill_name": skill, "requirement_level": level, "category": category}
            )

    # 逐行判定级别
    for line in lines:
        line_skills = _extract_skills(line)
        if not line_skills:
            continue
        level = "required"
        for pattern, lv in _LEVEL_PATTERNS:
            if pattern.search(line):
                level = lv
                break
        category = "软技能" if any(
            s in line for s in ("沟通", "团队", "管理", "英语")
        ) else "专业技能"
        for skill in line_skills:
            add_requirement(skill, level, category)

    # 兜底：全文扫一遍没抓到的技能
    for skill in _extract_skills(jd_text):
        add_requirement(skill, "required", "专业技能")

    title = None
    for line in lines[:5]:
        m = re.search(r"(岗位|职位)[:：]\s*(.+)", line)
        if m:
            title = m.group(2).strip()[:64]
            break
    if title is None and lines:
        first = lines[0]
        if len(first) <= 30 and not _extract_skills(first):
            title = first

    return {
        "title": title,
        "requirements": requirements,
        "summary": f"提取到 {len(requirements)} 条岗位要求",
    }
