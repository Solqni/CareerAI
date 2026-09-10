import api from './index'

export interface Job {
  id: number
  title: string
  jd_text: string
  parsed_json?: any
  created_at: string
  position_title?: string
}

export function parseJobDescription(jdText: string) {
  return api.post('/jobs/parse', { jd_text: jdText })
}

export function getJobs(): Promise<Job[]> {
  return api.get('/jobs').then(r => r.data)
}

export function createJob(data: Partial<Job>): Promise<Job> {
  return api.post('/jobs', data).then(r => r.data)
}

export function getJob(jobId: number) {
  return api.get(`/jobs/${jobId}`)
}