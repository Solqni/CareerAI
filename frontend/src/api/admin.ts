import api from './index'

export interface AdminUser {
  id: number
  username: string
  email: string | null
  role: string
}

export interface SystemInfo {
  user_count: number
  job_count: number
  match_report_count: number
  knowledge_doc_count: number
}

export interface AdminJob {
  id: number
  position_title: string | null
  company?: string | null
  city?: string | null
  source: string
  source_label: string
  is_shared: boolean
  owner_username: string
  requirement_count: number
  created_at: string
}

export interface CollectedJob {
  id: number
  position_title: string | null
  company?: string | null
  city?: string | null
}

export interface CollectJobsResult {
  source: string
  source_label: string
  keyword: string
  collected: CollectedJob[]
  collected_count: number
  failed_count: number
}

export interface CollectKnowledgeResult {
  topic: string
  documents: { id: number; title: string; chunk_count: number }[]
  generated_count: number
}

/** 用户列表（管理员专属） */
export async function listUsers(): Promise<AdminUser[]> {
  const resp = await api.get('/admin/users')
  return resp.data.data
}

/** 修改用户信息：用户名/邮箱/角色/密码（仅提交字段生效） */
export async function updateUser(
  userId: number,
  data: { username?: string; email?: string | null; role?: 'user' | 'admin'; password?: string }
): Promise<AdminUser> {
  const resp = await api.patch(`/admin/users/${userId}`, data)
  return resp.data.data
}

/** 修改用户角色（兼容旧用法） */
export async function updateUserRole(userId: number, role: 'user' | 'admin'): Promise<AdminUser> {
  return updateUser(userId, { role })
}

/** 删除用户及其全部业务数据（级联） */
export async function deleteUser(userId: number): Promise<void> {
  await api.delete(`/admin/users/${userId}`)
}

/** 系统统计（管理员专属） */
export async function getSystemInfo(): Promise<SystemInfo> {
  const resp = await api.get('/admin/system')
  return resp.data.data
}

/** 全平台岗位列表（含归属与来源） */
export async function listAdminJobs(): Promise<AdminJob[]> {
  const resp = await api.get('/admin/jobs')
  return resp.data.data
}

/** 删除任意岗位及其关联数据 */
export async function deleteAdminJob(jobId: number): Promise<void> {
  await api.delete(`/admin/jobs/${jobId}`)
}

/** AI 从招聘网站实时采集岗位（真实爬取，失败自动降级 AI 模拟） */
export async function collectJobsFromWeb(data: {
  keyword: string
  count: number
}): Promise<CollectJobsResult> {
  const resp = await api.post('/admin/jobs/ai-collect', data, { timeout: 300000 })
  return resp.data.data
}

/** AI 采集知识文档：按主题生成并走 RAG 链路入库 */
export async function collectKnowledge(data: {
  topic: string
  doc_count: number
}): Promise<CollectKnowledgeResult> {
  const resp = await api.post('/admin/knowledge/ai-collect', data, { timeout: 300000 })
  return resp.data.data
}
