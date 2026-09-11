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

// 匹配分析反馈
export interface MatchFeedback {
  feedback: string
  learning_plan: Array<{
    id: string
    title: string
    type: string
    priority: string
    estimated_time: string
    completed: boolean
  }>
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

// 生成匹配反馈和学习计划
export function generateMatchFeedback(matchId: string): Promise<MatchFeedback> {
  return fetch(`/match/${matchId}/feedback`)
    .then(response => response.json())
    .catch(error => {
      console.error('生成反馈失败:', error)
      throw error
    })
}

// 创建匹配（保留旧接口）
export function createMatch(data: { job_id: string; resume_data: any }) {
  return api.post('/match/create', data)
}