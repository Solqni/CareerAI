import api from './index'

export interface Job {
  id: string
  title: string
  jd_text: string
  parsed_json?: any
  created_at: string
}

export function parseJobDescription(jdText: string) {
  return api.post('/jobs/parse', { jd_text: jdText })
}

export function getJobs() {
  return api.get('/jobs')
}

export function createJob(data: Partial<Job>) {
  return api.post('/jobs', data)
}

export function getJob(jobId: number) {
  return api.get(`/jobs/${jobId}`)
}