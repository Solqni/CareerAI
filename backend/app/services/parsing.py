"""LLM 解析服务：简历解析 + JD 解析。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.client import get_chat_llm, get_vision_llm
from app.schemas.job import JDParsedResult, ParsedJobRequirement
from app.schemas.resume import (
    ParsedEducation,
    ParsedExperience,
    ParsedResumeAnalysis,
    ParsedSkill,
    ResumeParsedResult,
)

RESUME_SYSTEM_PROMPT = """你是一位资深的人力资源专家与简历分析顾问。请对以下简历文本完成两部分任务：完整提取结构化信息，并给出专业分析。

提取规则（非常重要）：
1. 尽最大努力提取简历中的所有信息，宁多勿漏；不要概括、压缩或改写原文细节
2. 每段经历（工作/实习/项目）的 description 必须完整转述原文中的全部要点：职责、技术方案、个人贡献、量化成果（数字、百分比、规模）等，不要省略任何内容
3. 提取教育经历（学校、学历、专业、时间）
4. 提取技能清单，评估熟练度（1-5 分），并分类（技术/工具/领域/软技能）
5. 提取证书、奖项荣誉、语言能力、求职意向（如有）
6. 如果某项信息在简历中不存在，设为 null 或空列表，绝对不要编造

分析规则：
7. summary：用 3-5 句概括候选人整体情况（教育背景、工作年限、专业方向、整体竞争力）
8. highlights：提炼 3-6 条最有价值的简历亮点，每条引用原文中的事实支撑（如项目成果、技术栈、证书）
9. analysis.strengths：核心优势 2-5 条；analysis.weaknesses：简历中的短板或缺失项 2-5 条（如缺少量化成果、经历空窗、无证书等，确实没有则返回空列表）
10. analysis.estimated_years：根据工作/实习经历时间跨度推算工作年限（如"约 3 年"）
11. analysis.career_summary：综合评价 2-4 句（发展轨迹、能力侧重、适合的岗位方向）

请以 JSON 格式返回，严格按照以下结构：
{
  "name": "姓名或null",
  "email": "邮箱或null",
  "phone": "电话或null",
  "education": [{"school": "学校", "degree": "学历", "major": "专业", "date_range": "时间或null"}],
  "skills": [{"skill_name": "技能名", "proficiency": 1-5, "category": "技术/工具/领域/软技能或null"}],
  "experiences": [{"type": "work/internship/project", "title": "标题", "description": "完整描述（保留原文全部细节与量化成果）", "date_range": "时间或null"}],
  "certificates": ["证书1", "证书2"],
  "awards": ["奖项1"],
  "languages": ["英语 CET-6"],
  "job_intention": "求职意向或null",
  "summary": "整体概括 3-5 句",
  "highlights": ["亮点1", "亮点2"],
  "analysis": {
    "estimated_years": "约 X 年或null",
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["待提升1"],
    "career_summary": "综合评价或null"
  }
}"""


JD_SYSTEM_PROMPT = """你是一位专业的岗位分析专家。请从以下岗位描述（JD）中提取结构化信息。

解析规则：
1. 提取岗位名称
2. 提取岗位职责列表
3. 提取技能要求，标注是"必须"(must)还是"加分"(plus)，并分类（技术/工具/领域/软技能）
4. 提取学历要求
5. 提取经验要求（如"3年以上"）
6. 生成一段岗位概述
7. 如果某项信息不存在，请设为 null 或空列表

请以 JSON 格式返回，严格按照以下结构：
{
  "position_title": "岗位名称或null",
  "responsibilities": ["职责1", "职责2"],
  "required_skills": [{"skill_name": "技能名", "requirement_level": "must或plus", "category": "技术/工具/领域/软技能或null"}],
  "education_requirement": "学历要求或null",
  "experience_requirement": "经验要求或null",
  "summary": "概述或null"
}"""


def _parse_json_response(text: str) -> dict:
    """从 LLM 响应中提取 JSON，兼容 markdown 代码块包裹。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


async def parse_resume(raw_text: str) -> ResumeParsedResult:
    """调用 LLM 解析简历文本，返回结构化结果。"""
    llm = get_chat_llm()
    messages = [
        SystemMessage(content=RESUME_SYSTEM_PROMPT),
        HumanMessage(content=raw_text),
    ]
    response = await llm.ainvoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    data = _parse_json_response(content)

    result = ResumeParsedResult(
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        education=[ParsedEducation(**edu) for edu in data.get("education", []) if isinstance(edu, dict)],
        skills=[ParsedSkill(**s) for s in data.get("skills", []) if isinstance(s, dict)],
        experiences=[ParsedExperience(**exp) for exp in data.get("experiences", []) if isinstance(exp, dict)],
        certificates=[str(c) for c in data.get("certificates", []) if c],
        awards=[str(a) for a in data.get("awards", []) if a],
        languages=[str(l) for l in data.get("languages", []) if l],
        job_intention=data.get("job_intention"),
        summary=data.get("summary"),
        highlights=[str(h) for h in data.get("highlights", []) if h],
        analysis=(
            ParsedResumeAnalysis(**data["analysis"])
            if isinstance(data.get("analysis"), dict)
            else None
        ),
    )
    return result


async def parse_jd(jd_text: str) -> JDParsedResult:
    """调用 LLM 解析 JD 文本，返回结构化结果。"""
    llm = get_chat_llm()
    messages = [
        SystemMessage(content=JD_SYSTEM_PROMPT),
        HumanMessage(content=jd_text),
    ]
    response = await llm.ainvoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    data = _parse_json_response(content)

    result = JDParsedResult(
        position_title=data.get("position_title"),
        responsibilities=data.get("responsibilities", []),
        required_skills=[ParsedJobRequirement(**s) for s in data.get("required_skills", [])],
        education_requirement=data.get("education_requirement"),
        experience_requirement=data.get("experience_requirement"),
        summary=data.get("summary"),
    )
    return result


JD_IMAGE_PROMPT = """你是一位专业的岗位信息提取助手。请从这张图片中提取完整的岗位描述（JD）文字内容。

要求：
1. 逐字提取图片中与岗位相关的所有文字，保持原始顺序和段落结构
2. 包括岗位名称、岗位职责、任职要求、技能要求、薪资待遇、公司信息等
3. 不要添加图片中不存在的内容，不要总结或改写
4. 如果图片中没有岗位相关的文字内容，只返回"NO_JD_CONTENT"

直接返回提取的纯文本，不要包含任何解释。"""


async def extract_jd_text_from_image(image_data_url: str) -> str:
    """调用视觉 LLM 识别图片中的 JD 文本，返回纯文本。

    image_data_url: 形如 data:image/png;base64,xxx 的图片 Data URL。
    """
    llm = get_vision_llm()
    message = HumanMessage(
        content=[
            {"type": "image_url", "image_url": {"url": image_data_url}},
            {"type": "text", "text": JD_IMAGE_PROMPT},
        ]
    )
    response = await llm.ainvoke([message])
    content = response.content if isinstance(response.content, str) else str(response.content)
    text = content.strip()

    if not text or "NO_JD_CONTENT" in text:
        raise ValueError("无法从图片中识别出岗位描述内容，请确认图片包含完整的 JD 文字")
    return text
