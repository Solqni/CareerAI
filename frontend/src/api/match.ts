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
  return api.post<MatchAnalysisResult>('/match/analyze', data).then(r => r.data)
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

// 创建匹配（保留旧接口）
export function createMatch(data: { job_id: string; resume_data: any }) {
  return api.post('/match/create', data)
}