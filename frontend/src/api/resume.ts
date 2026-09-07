import api from './index'

/** 粘贴文本解析简历 */
export function parseResumeText(raw_text: string) {
  return api.post('/resume/parse', { raw_text })
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
