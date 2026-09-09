import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMatches, createMatch, type MatchResult } from '@/api/match'

export const useMatchStore = defineStore('match', () => {
  const matches = ref<MatchResult[]>([])
  const loading = ref(false)
  const error = ref('')

  // 获取匹配结果列表
  async function fetchMatches() {
    try {
      loading.value = true
      error.value = ''
      matches.value = await getMatches()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取匹配结果失败'
    } finally {
      loading.value = false
    }
  }

  // 创建新的匹配
  async function createNewMatch(jobId: string, resumeData: any) {
    try {
      loading.value = true
      error.value = ''
      const result = await createMatch({ job_id: jobId, resume_data: resumeData })
      // 添加到匹配列表
      matches.value.unshift(result)
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || '创建匹配失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除匹配结果
  async function deleteMatch(matchId: string) {
    try {
      loading.value = true
      error.value = ''
      // TODO: 实现删除匹配的API调用
      // 从本地列表中移除
      matches.value = matches.value.filter(m => m.id !== matchId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || '删除匹配失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    matches,
    loading,
    error,
    fetchMatches,
    createNewMatch,
    deleteMatch
  }
})