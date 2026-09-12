import api from './index'

export interface Job {
  id: number
  title: string
  jd_text: string
  parsed_json?: any
  created_at: string
  position_title?: string
  is_shared?: boolean
  is_owner?: boolean
}

export function parseJobDescription(jdText: string) {
  return api.post('/jobs/parse', { jd_text: jdText })
}

// 上传 JD 截图，视觉模型识别后解析
export function parseJobImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/jobs/parse-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000
  })
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

/** 删除本人岗位分析（后端级联清理其报告/学习计划链，解除面试会话引用） */
export function deleteJob(jobId: number) {
  return api.delete(`/jobs/${jobId}`)
}