import api from './index'

export interface MatchResult {
  id: string
  job_id: string
  job_title: string
  score: number
  skills_match: number
  experience_match: number
  education_match: number
  created_at: string
  feedback?: string
}

export function getMatches() {
  return api.get('/match/list')
}

export function createMatch(data: { job_id: string; resume_data: any }) {
  return api.post('/match/create', data)
}

export function getMatchDetail(matchId: string) {
  return api.get(`/match/${matchId}`)
}