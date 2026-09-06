import api from './index'

/** 解析 JD 文本 */
export function parseJobDescription(jd_text: string) {
  return api.post('/jobs/parse', { jd_text }, { timeout: 60000 })
}
