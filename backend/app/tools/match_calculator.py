"""匹配度计算工具

实现简历与岗位的匹配度计算，包括：
- 技能匹配度计算
- 经验匹配度计算
- 教育匹配度计算
- 综合评分算法
- 差距分析逻辑
- 学习建议生成
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from math import sqrt

from enum import Enum

from app.models.match import MatchReport, GapItem, Recommendation
from app.models.resume import UserSkill, UserExperience
from app.models.resume_model import Resume
from app.models.job import JobAnalysis, JobRequirement
from app.schemas.job import JDParsedResult
from app.models.user import User
from app.schemas.user import UserOut


class GapSeverity(str, Enum):
    """差距严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def calculate_skill_match(
    resume_skills: List[UserSkill],
    job_requirements: List[JobRequirement]
) -> float:
    """计算技能匹配度

    Args:
        resume_skills: 用户技能列表
        job_requirements: 岗位要求列表

    Returns:
        技能匹配度 (0-100)
    """
    if not job_requirements:
        return 100.0  # 无技能要求则认为完全匹配

    # 将用户技能转换为字典 {skill_name: proficiency}
    resume_skill_dict = {skill.skill_name.lower(): skill.proficiency for skill in resume_skills}

    # 计算每个技能要求的匹配情况
    total_score = 0.0
    max_score = len(job_requirements) * 100

    for job_req in job_requirements:
        skill_name = job_req.skill_name.lower()
        required_proficiency = job_req.level or 80  # 默认要求80分

        if skill_name in resume_skill_dict:
            user_proficiency = resume_skill_dict[skill_name]
            # 如果用户技能达到要求，给100分，否则按比例扣分
            if user_proficiency >= required_proficiency:
                total_score += 100
            else:
                # 按熟练度比例扣分，但最低不低于0
                total_score += max(0, (user_proficiency / required_proficiency) * 100)
        else:
            # 技能缺失，给0分
            total_score += 0

    # 计算匹配度
    if max_score == 0:
        return 100.0

    return (total_score / max_score) * 100


def calculate_experience_match(
    resume_experiences: List[UserExperience],
    job_experience_requirement: Optional[str] = None
) -> float:
    """计算经验匹配度

    Args:
        resume_experiences: 用户经历列表
        job_experience_requirement: 岗位经验要求

    Returns:
        经验匹配度 (0-100)
    """
    if not job_experience_requirement:
        return 100.0  # 无经验要求则认为完全匹配

    # 解析岗位经验要求
    experience_years = parse_experience_requirement(job_experience_requirement)

    if not experience_years:
        return 100.0

    # 计算用户相关工作经验年限
    relevant_experience_years = calculate_relevant_experience(
        resume_experiences,
        experience_years
    )

    # 如果用户经验达到或超过要求，给100分，否则按比例扣分
    if relevant_experience_years >= experience_years:
        return 100.0
    else:
        return (relevant_experience_years / experience_years) * 100


def calculate_education_match(
    resume_education: Optional[str],
    job_education_requirement: Optional[str] = None
) -> float:
    """计算教育匹配度

    Args:
        resume_education: 用户教育背景
        job_education_requirement: 岗位教育要求

    Returns:
        教育匹配度 (0-100)
    """
    if not job_education_requirement:
        return 100.0  # 无教育要求则认为完全匹配

    # 教育等级映射
    education_levels = {
        '博士': 5,
        '硕士': 4,
        '本科': 3,
        '大专': 2,
        '高中': 1,
        '中专': 1,
    }

    job_level = education_levels.get(job_education_requirement, 0)
    resume_level = education_levels.get(resume_education, 0)

    if job_level == 0:
        return 100.0

    # 如果用户学历达到或超过要求，给100分，否则按比例扣分
    if resume_level >= job_level:
        return 100.0
    else:
        # 按学历等级比例扣分
        return (resume_level / job_level) * 100


def analyze_gaps(
    resume: Resume,
    job: JobAnalysis,
    job_parsed: Optional[JDParsedResult] = None
) -> List[GapItem]:
    """分析简历与岗位的差距

    Args:
        resume: 简历数据
        job: 岗位分析数据
        job_parsed: 岗位解析结果

    Returns:
        差距项列表
    """
    gaps = []

    # 获取岗位解析结果
    if job_parsed is None:
        from app.schemas.job import JDParsedResult
        job_parsed = JDParsedResult(**job.parsed_json)

    # 技能差距分析
    resume_skills = resume.user_skills if hasattr(resume, 'user_skills') else []
    required_skills = job_parsed.required_skills

    for req_skill in required_skills:
        skill_found = False
        for user_skill in resume_skills:
            if user_skill.skill_name.lower() == req_skill.skill_name.lower():
                skill_found = True
                # 检查熟练度是否达到要求
                required_level = req_skill.level or 80
                if user_skill.proficiency < required_level:
                    gaps.append(GapItem(
                        type='skill',
                        skill_name=req_skill.skill_name,
                        current_level=user_skill.proficiency,
                        target_level=required_level,
                        severity=GapSeverity.MEDIUM if user_skill.proficiency > required_level * 0.7 else GapSeverity.HIGH,
                        description=f'技能熟练度不足，当前 {user_skill.proficiency}，要求 {required_level}'
                    ))
                break

        if not skill_found:
            gaps.append(GapItem(
                type='skill',
                skill_name=req_skill.skill_name,
                current_level=0,
                target_level=req_skill.level or 80,
                severity=GapSeverity.HIGH,
                description=f'缺少技能 {req_skill.skill_name}'
            ))

    # 经验差距分析
    if job_parsed.experience_requirement:
        experience_years = parse_experience_requirement(job_parsed.experience_requirement)
        if experience_years:
            relevant_years = calculate_relevant_experience(
                resume.user_experiences if hasattr(resume, 'user_experiences') else [],
                experience_years
            )

            if relevant_years < experience_years:
                gaps.append(GapItem(
                    type='experience',
                    experience_type=get_experience_type(job_parsed.position_title or ''),
                    current_years=relevant_years,
                    target_years=experience_years,
                    severity=GapSeverity.HIGH if relevant_years < experience_years * 0.5 else GapSeverity.MEDIUM,
                    description=f'经验不足，要求 {experience_years} 年，目前 {relevant_years} 年'
                ))

    # 教育差距分析
    if job_parsed.education_requirement:
        resume_level = get_education_level(resume.profile.education if hasattr(resume, 'profile') and resume.profile.education else None)
        job_level = get_education_level(job_parsed.education_requirement)

        if resume_level < job_level:
            gaps.append(GapItem(
                type='education',
                current_education=resume.profile.education if hasattr(resume, 'profile') and resume.profile.education else '未知',
                target_education=job_parsed.education_requirement,
                severity=GapSeverity.MEDIUM,
                description=f'教育背景不足，要求 {job_parsed.education_requirement}'
            ))

    return gaps


def generate_recommendations(gaps: List[GapItem]) -> List[Recommendation]:
    """生成学习建议

    Args:
        gaps: 差距项列表

    Returns:
        学习建议列表
    """
    recommendations = []

    for gap in gaps:
        if gap.type == 'skill':
            recommendations.append(Recommendation(
                type='学习技能',
                description=f'建议学习 {gap.skill_name} 技能，当前熟练度 {gap.current_level}，目标熟练度 {gap.target_level}',
                priority=gap.severity,
                estimated_time=estimate_learning_time(gap.skill_name, gap.target_level - gap.current_level)
            ))
        elif gap.type == 'experience':
            recommendations.append(Recommendation(
                type='补充经验',
                description=f'建议增加 {gap.experience_type} 相关经验，目标 {gap.target_years} 年',
                priority=gap.severity,
                estimated_time=f'{gap.target_years - gap.current_years} 年'
            ))
        elif gap.type == 'education':
            recommendations.append(Recommendation(
                type='提升学历',
                description=f'建议提升学历至 {gap.target_education}',
                priority=gap.severity,
                estimated_time='2-4 年'
            ))

    # 按优先级排序
    recommendations.sort(key=lambda x: x.priority.value, reverse=True)

    return recommendations


def calculate_match(
    resume: Resume,
    job: JobAnalysis
) -> MatchReport:
    """计算简历与岗位的匹配度

    Args:
        resume: 简历数据
        job: 岗位分析数据

    Returns:
        匹配报告
    """
    # 解析岗位数据
    from app.schemas.job import JDParsedResult
    job_parsed = JDParsedResult(**job.parsed_json)

    # 计算各项匹配度
    skill_match = calculate_skill_match(
        resume.user_skills if hasattr(resume, 'user_skills') else [],
        job_parsed.required_skills
    )

    experience_match = calculate_experience_match(
        resume.user_experiences if hasattr(resume, 'user_experiences') else [],
        job_parsed.experience_requirement
    )

    education_match = calculate_education_match(
        resume.profile.education if hasattr(resume, 'profile') and resume.profile.education else None,
        job_parsed.education_requirement
    )

    # 综合评分（技能权重50%，经验权重30%，教育权重20%）
    overall_score = (skill_match * 0.5 + experience_match * 0.3 + education_match * 0.2)

    # 差距分析
    gaps = analyze_gaps(resume, job, job_parsed)

    # 生成建议
    recommendations = generate_recommendations(gaps)

    return MatchReport(
        user_id=resume.user_id,
        job_id=job.id,
        position_title=job_parsed.position_title or '',
        skill_match=round(skill_match, 2),
        experience_match=round(experience_match, 2),
        education_match=round(education_match, 2),
        overall_score=round(overall_score, 2),
        gaps=gaps,
        recommendations=recommendations,
        created_at=datetime.now(),
        analyzed_at=datetime.now()
    )


# 辅助函数
def parse_experience_requirement(experience_str: str) -> Optional[int]:
    """解析经验要求字符串，提取年限"""
    import re

    # 匹配类似 "3-5年" 或 "3年" 或 "3年以上" 的模式
    patterns = [
        r'(\d+)\s*-\s*(\d+)\s*年',
        r'(\d+)\s*年',
        r'(\d+)\s*年以上'
    ]

    for pattern in patterns:
        match = re.search(pattern, experience_str)
        if match:
            if '-' in pattern:
                # 取平均值
                years = (int(match.group(1)) + int(match.group(2))) / 2
            else:
                years = int(match.group(1))

            # 如果是"以上"，假设为要求的2倍
            if '以上' in experience_str:
                years = min(years * 2, 10)  # 最多按10年计算

            return int(years)

    return None


def calculate_relevant_experience(experiences: List[UserExperience], target_years: int) -> float:
    """计算相关工作经验年限

    Args:
        experiences: 用户经历列表
        target_years: 目标年限

    Returns:
        相关工作经验年限
    """
    relevant_experience = 0.0

    for exp in experiences:
        # 简单判断：如果是开发相关岗位，只计算技术相关经验
        if exp.type in ['work', 'project']:
            # 这里简化处理，实际应该根据岗位类型判断相关性
            # 假设每段经验都是相关的
            duration = parse_experience_duration(exp.date_range)
            relevant_experience += duration

    return min(relevant_experience, target_years)


def parse_experience_duration(date_range: Optional[str]) -> float:
    """解析经历持续时间"""
    if not date_range:
        return 0.0

    # 这里简化处理，实际应该解析具体的起止日期
    # 假设平均每段工作经历1年
    return 1.0


def get_experience_type(position_title: str) -> str:
    """根据岗位类型返回经验类型"""
    if '开发' in position_title or '工程师' in position_title:
        return '技术开发'
    elif '设计' in position_title:
        return '设计'
    elif '产品' in position_title:
        return '产品'
    elif '运营' in position_title:
        return '运营'
    else:
        return '相关工作'


def get_education_level(education_str: Optional[str]) -> int:
    """获取教育等级"""
    if not education_str:
        return 0

    education_levels = {
        '博士': 5,
        '硕士': 4,
        '本科': 3,
        '大专': 2,
        '高中': 1,
        '中专': 1,
    }

    return education_levels.get(education_str, 0)


def estimate_learning_time(skill_name: str, proficiency_gap: int) -> str:
    """估算学习时间"""
    # 基础技能
    basic_skills = ['python', 'javascript', 'java', 'c++', 'sql', 'html', 'css']

    if skill_name.lower() in basic_skills:
        if proficiency_gap <= 20:
            return '1-2周'
        elif proficiency_gap <= 40:
            return '3-4周'
        else:
            return '2-3个月'
    else:
        # 专业技能
        if proficiency_gap <= 20:
            return '2-4周'
        elif proficiency_gap <= 40:
            return '4-8周'
        else:
            return '3-6个月'