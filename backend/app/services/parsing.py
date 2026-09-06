"""LLM 解析服务：简历解析 + JD 解析。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.client import get_chat_llm
from app.schemas.job import JDParsedResult, ParsedJobRequirement
from app.schemas.resume import (
    ParsedEducation,
    ParsedExperience,
    ParsedSkill,
    ResumeParsedResult,
)

RESUME_SYSTEM_PROMPT = """你是一位专业的简历解析专家。请从以下简历文本中提取结构化信息。

解析规则：
1. 从文本中提取姓名、邮箱、电话等基本信息
2. 提取教育经历（学校、学历、专业、时间）
3. 提取技能清单，并评估熟练度（1-5分）
4. 提取工作/项目经历（类型、职位、描述、时间）
5. 生成一段简短的个人概述
6. 如果某项信息在简历中不存在，请设为 null 或空列表

请以 JSON 格式返回，严格按照以下结构：
{
  "name": "姓名或null",
  "email": "邮箱或null",
  "phone": "电话或null",
  "education": [{"school": "学校", "degree": "学历", "major": "专业", "date_range": "时间或null"}],
  "skills": [{"skill_name": "技能名", "proficiency": 1-5}],
  "experiences": [{"type": "work/internship/project", "title": "标题", "description": "描述或null", "date_range": "时间或null"}],
  "summary": "概述或null"
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
        education=[ParsedEducation(**e) for e in data.get("education", [])],
        skills=[ParsedSkill(**s) for s in data.get("skills", [])],
        experiences=[ParsedExperience(**e) for e in data.get("experiences", [])],
        summary=data.get("summary"),
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