import api from './index'

export interface Skill {
  id: number
  skill_name: string
  proficiency: number
  source: string
}

export interface ParsedExperience {
  type: string | null
  title: string | null
  description: string | null
  date_range: string | null
}

export interface ParsedEducation {
  school: string | null
  degree: string | null
  major: string | null
  date_range: string | null
}

export interface Profile {
  username: string
  email: string | null
  phone: string | null
  education: string | null
  education_details: ParsedEducation[]
  skills: Skill[]
  experiences: string[]
  experiences_details: ParsedExperience[]
  summary: string | null
  /** 最新简历解析完整结果（含证书/奖项/语言/求职意向/亮点/分析） */
  parsed_json?: any
}

/** 获取用户能力画像（最新简历解析结果 + 技能表合并） */
export async function getProfile(): Promise<Profile> {
  try {
    const { data } = await api.get<Profile>('/resume/profile')
    return data
  } catch (error) {
    console.error('获取能力画像失败:', error)
    throw error
  }
}

/** 粘贴文本解析简历 */
export function parseResumeText(raw_text: string) {
  return api.post('/resume/parse', { raw_text }, { timeout: 120000 })
}

/** 上传文件解析简历 */
export function uploadResumeFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}
