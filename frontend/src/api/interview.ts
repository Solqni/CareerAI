import api from './index'

// 面试题类型（M5：技术题 / 项目题 / 行为题）
export type InterviewCategory = 'technical' | 'project' | 'behavioral'

export interface GeneratedQuestion {
  category: InterviewCategory
  question: string
}

// 单轮回答的多维度评估
export interface FeedbackJSON {
  scores: {
    logic: number
    completeness: number
    professionalism: number
  }
  overall: number
  strengths: string
  weaknesses: string
  suggestions: string
  source: 'llm' | 'fallback'
}

export interface InterviewQA {
  id: number
  session_id: number
  category: string
  question: string
  answer: string | null
  score: number | null
  feedback: string | null
  feedback_json: FeedbackJSON | null
}

export interface InterviewSession {
  id: number
  user_id: number
  job_id: number | null
  resume_id: number | null
  position_title?: string | null
  status: 'active' | 'finished' | string
  summary?: string | null
  created_at: string
  finished_at?: string | null
  qas: InterviewQA[]
}

export interface SessionListItem {
  id: number
  job_id: number | null
  position_title?: string | null
  status: string
  created_at: string
  finished_at?: string | null
  qa_count: number
  answered_count: number
  average_score: number | null
}

export interface AnswerResult {
  qa: InterviewQA
  next_qa: InterviewQA | null
  is_finished: boolean
}

/** 创建模拟面试会话（同时由 LLM 生成题库，耗时较长） */
export function createInterviewSession(data: {
  job_id: number
  resume_id?: number
  question_count?: number
}): Promise<InterviewSession> {
  return api
    .post<InterviewSession>('/interview/session', data, { timeout: 180000 })
    .then(r => r.data)
}

/** 获取面试会话历史列表 */
export function listInterviewSessions(): Promise<SessionListItem[]> {
  return api.get<SessionListItem[]>('/interview/sessions').then(r => r.data)
}

/** 获取面试会话详情（含全部问答与评估） */
export function getInterviewSession(id: number): Promise<InterviewSession> {
  return api.get<InterviewSession>(`/interview/session/${id}`).then(r => r.data)
}

/** 提交一轮回答，返回三维度评估与下一道题 */
export function submitAnswer(
  sessionId: number,
  qaId: number,
  answer: string
): Promise<AnswerResult> {
  return api
    .post<AnswerResult>(
      `/interview/session/${sessionId}/answer`,
      { qa_id: qaId, answer },
      { timeout: 120000 }
    )
    .then(r => r.data)
}

/** 结束面试并生成总评报告 */
export function finishInterview(sessionId: number): Promise<InterviewSession> {
  return api
    .post<InterviewSession>(`/interview/session/${sessionId}/finish`, {}, { timeout: 180000 })
    .then(r => r.data)
}

/** 仅生成面试题（不开面试会话） */
export function generateInterviewQuestions(data: {
  job_id: number
  resume_id?: number
  question_count?: number
}): Promise<{
  job_id: number
  position_title?: string | null
  questions: GeneratedQuestion[]
  source: string
}> {
  return api
    .post('/interview/questions', data, { timeout: 180000 })
    .then(r => r.data)
}

// 题型展示配置
export const categoryMeta: Record<string, { label: string; color: string }> = {
  technical: { label: '技术题', color: '#667eea' },
  project: { label: '项目题', color: '#764ba2' },
  behavioral: { label: '行为题', color: '#f093fb' },
}
