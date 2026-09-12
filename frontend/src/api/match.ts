import api from './index'

// 匹配分析请求接口
export interface MatchAnalysisRequest {
  resume_id: number
  job_id: number
}

// 差距项接口
export interface GapItem {
  type: string
  skill_name?: string
  current_level?: number
  target_level?: number
  current_years?: number
  target_years?: number
  current_education?: string
  target_education?: string
  experience_type?: string
  severity: 'low' | 'medium' | 'high'
  description: string
}

// 建议接口
export interface Recommendation {
  type: string
  description: string
  priority: 'low' | 'medium' | 'high'
  estimated_time?: string
}

// 匹配分析结果接口
export interface MatchAnalysisResult {
  id: string
  user_id: number
  job_id: number
  position_title: string
  skill_match: number
  experience_match: number
  education_match: number
  overall_score: number
  summary?: string
  company?: string | null
  city?: string | null
  detail_json?: { analysis_source?: string; rule_summary?: string } | null
  gaps: GapItem[]
  recommendations: Recommendation[]
  created_at: string
  analyzed_at: string
}

// 匹配列表项接口
export interface MatchListItem {
  id: string
  job_id: number
  position_title: string
  overall_score: number
  skill_match: number
  experience_match: number
  education_match: number
  created_at: string
  analyzed_at: string
}

// 学习任务学习内容（知识点来自管理员知识库检索，练习题首次生成后缓存）
export interface StudyKnowledgeItem {
  content: string
  doc_title: string
  similarity: number
}

export interface StudyQuestionItem {
  question: string
  reference_answer: string
}

export interface StudyAnswerFeedback {
  answer: string
  feedback: string
  score?: number | null
}

export interface TaskStudy {
  task_id: number
  task_name: string
  knowledge: StudyKnowledgeItem[]
  questions: StudyQuestionItem[]
  answers: Record<string, StudyAnswerFeedback>
  batch: number
  total_generated: number
  source: 'cache' | 'llm' | 'rag_only'
}

// 仪表盘学习进度（用户最新一份学习计划的真实完成度）
export interface ProgressTaskItem {
  id: number
  task_name: string
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high'
}

export interface LearningProgress {
  has_plan: boolean
  position_title?: string | null
  total_tasks: number
  done_tasks: number
  in_progress_tasks: number
  progress: number
  tasks: ProgressTaskItem[]
}

// 学习任务接口
export interface LearningTask {
  id: number
  plan_id: number
  task_name: string
  description?: string
  resource_url?: string
  priority: 'low' | 'medium' | 'high'
  estimated_days?: number
  status: 'todo' | 'in_progress' | 'done'
  due_date?: string
}

// 学习计划接口
export interface LearningPlan {
  id: number
  user_id: number
  report_id: string
  content_json?: { tasks?: Array<Record<string, unknown>>; source?: string }
  status: string
  tasks: LearningTask[]
}

// 分析匹配度
export function analyzeMatch(data: MatchAnalysisRequest): Promise<MatchAnalysisResult> {
  // 完整匹配含 LLM 学习计划生成（实测 1-2 分钟），放宽超时到 5 分钟
  return api.post<MatchAnalysisResult>('/match/analyze', data, { timeout: 300000 }).then(r => r.data)
}

// 获取匹配列表
export function getMatches(): Promise<MatchListItem[]> {
  return api.get('/match/')
    .then(response => response.data.reports || [])
    .catch(error => {
      console.error('获取匹配结果失败:', error)
      return []
    })
}

// 获取匹配详情
export function getMatchDetail(matchId: string): Promise<MatchAnalysisResult> {
  return api.get<MatchAnalysisResult>(`/match/${matchId}`).then(r => r.data)
}

// 获取匹配报告对应的学习计划（含任务列表）
export function getMatchPlan(matchId: string): Promise<LearningPlan> {
  return api.get<LearningPlan>(`/match/${matchId}/plan`).then(r => r.data)
}

// 更新学习任务状态（todo: 待开始 / in_progress: 进行中 / done: 已完成）
export function updateTaskStatus(taskId: number, status: LearningTask['status']): Promise<LearningTask> {
  return api.patch<LearningTask>(`/match/plan/tasks/${taskId}`, { status }).then(r => r.data)
}

// 学习内容相关接口需现场调用 LLM（出题/点评耗时 10~70s），超时放宽到 3 分钟
const LLM_TIMEOUT = 180000

// 获取学习任务的学习内容（关联知识点 + 当前一批练习题 + 作答记录；无缓存题目时会现场生成）
export function getTaskStudy(taskId: number): Promise<TaskStudy> {
  return api.get<TaskStudy>(`/match/plan/tasks/${taskId}/study`, { timeout: LLM_TIMEOUT }).then(r => r.data)
}

// 换一批新题（旧题并入历史，新题不与历史重复，作答记录清空）
export function refreshTaskStudy(taskId: number): Promise<TaskStudy> {
  return api.post<TaskStudy>(`/match/plan/tasks/${taskId}/study/refresh`, null, { timeout: LLM_TIMEOUT }).then(r => r.data)
}

// 提交练习题作答，返回 AI 点评（得分 + 反馈）
export function submitTaskAnswer(
  taskId: number,
  question: string,
  answer: string
): Promise<{ question: string; answer: string; feedback: string; score?: number | null }> {
  return api
    .post(`/match/plan/tasks/${taskId}/study/answer`, { question, answer }, { timeout: LLM_TIMEOUT })
    .then(r => r.data)
}

// 获取仪表盘学习进度（最新学习计划的真实完成度）
export function getLearningProgress(): Promise<LearningProgress> {
  return api.get<LearningProgress>('/match/progress').then(r => r.data)
}

// 创建匹配（保留旧接口）
export function createMatch(data: { job_id: string; resume_data: any }) {
  return api.post('/match/create', data)
}