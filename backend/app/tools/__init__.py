"""Tool Calling 工具集。

需求要求不少于 4 个具有业务意义的 Tool，真实连接 DB / RAG：
- parse_resume: 解析简历文本，调用 LLM 提取结构化信息并存入 DB
- parse_jd: 解析岗位描述，提取岗位要求并存入 DB
- calculate_match: 查询用户技能与岗位要求，计算匹配度
- search_knowledge: 在 RAG 知识库中检索
- generate_plan: 基于差距分析生成学习计划
- generate_interview_q: 生成面试题

本目录为占位结构，各工具后续单独实现。
"""
