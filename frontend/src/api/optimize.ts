import api from './index'

// 优化维度
export type OptimizeDimension = 'keyword' | 'quantify' | 'enhance' | 'structure'

// 单条优化建议
export interface OptimizationSuggestion {
  dimension: OptimizeDimension
  issue: string
  suggestion: string
  example?: string
}

// 知识库引用来源（来自平台管理员知识库）
export interface KnowledgeRef {
  doc_id: number
  doc_title: string
  similarity: number
}

// 简历优化结果
export interface OptimizeResponse {
  job_id: number
  position_title?: string
  resume_id?: number
  suggestions: OptimizationSuggestion[]
  summary?: string
  knowledge_refs?: KnowledgeRef[]
}

// 生成简历优化建议（M4：关键词优化/经历量化/内容增强/结构建议）
// 生成含 LLM 调用与 RAG 检索（实测 10-70s+），超时放宽到 3 分钟
export function optimizeResume(data: { job_id: number; resume_id?: number }): Promise<OptimizeResponse> {
  return api.post<OptimizeResponse>('/optimize', data, { timeout: 180000 }).then(r => r.data)
}

// 优化维度显示配置
export const dimensionMeta: Record<OptimizeDimension, { label: string; color: string }> = {
  keyword: { label: '关键词优化', color: '#8b5cf6' },
  quantify: { label: '经历量化', color: '#06b6d4' },
  enhance: { label: '内容增强', color: '#10b981' },
  structure: { label: '结构建议', color: '#f59e0b' },
}
