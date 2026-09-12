import api from './index'

export interface KnowledgeDoc {
  id: number
  title: string
  file_type: string
  chunk_count: number
}

/** 知识库文档列表 */
export async function listDocuments(): Promise<KnowledgeDoc[]> {
  const resp = await api.get('/knowledge/')
  return resp.data.data
}

/** 上传知识库文档（管理员专属，自动切分向量化） */
export async function uploadDocument(file: File): Promise<KnowledgeDoc> {
  const form = new FormData()
  form.append('file', file)
  const resp = await api.post('/knowledge/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
  return resp.data.data
}

/** 删除知识库文档（管理员专属） */
export async function deleteDocument(docId: number): Promise<void> {
  await api.delete(`/knowledge/${docId}`)
}
