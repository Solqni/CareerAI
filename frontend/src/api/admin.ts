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

/** 用户列表（管理员专属） */
export async function listUsers(): Promise<AdminUser[]> {
  const resp = await api.get('/admin/users')
  return resp.data.data
}

/** 修改用户角色（管理员专属） */
export async function updateUserRole(userId: number, role: 'user' | 'admin'): Promise<AdminUser> {
  const resp = await api.patch(`/admin/users/${userId}`, { role })
  return resp.data.data
}

/** 系统统计（管理员专属） */
export async function getSystemInfo(): Promise<SystemInfo> {
  const resp = await api.get('/admin/system')
  return resp.data.data
}
