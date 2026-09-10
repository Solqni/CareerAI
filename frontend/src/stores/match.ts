import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getMatches,
  analyzeMatch,
  getMatchDetail,
  type MatchAnalysisRequest,
  type MatchAnalysisResult,
  type MatchListItem,
  type MatchFeedback
} from '@/api/match'

export const useMatchStore = defineStore('match', () => {
  // 匹配列表
  const matches = ref<MatchListItem[]>([])
  // 当前分析的匹配详情
  const currentMatch = ref<MatchAnalysisResult | null>(null)
  // 匹配反馈和学习计划
  const matchFeedback = ref<MatchFeedback | null>(null)

  const loading = ref(false)
  const error = ref('')

  // 获取匹配结果列表
  async function fetchMatches() {
    try {
      loading.value = true
      error.value = ''
      const reports = await getMatches()
      matches.value = reports || []
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取匹配结果失败'
      console.error('获取匹配结果失败:', err)
      matches.value = []
    } finally {
      loading.value = false
    }
  }

  // 分析简历与岗位的匹配度
  async function analyzeMatchData(data: MatchAnalysisRequest) {
    try {
      loading.value = true
      error.value = ''
      const result = await analyzeMatch(data)
      currentMatch.value = result
      // 添加到匹配列表
      const listItem: MatchListItem = {
        id: result.id,
        job_id: result.job_id,
        position_title: result.position_title,
        overall_score: result.overall_score,
        skill_match: result.skill_match,
        experience_match: result.experience_match,
        education_match: result.education_match,
        created_at: result.created_at,
        analyzed_at: result.analyzed_at
      }
      matches.value.unshift(listItem)
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || '匹配分析失败'
      console.error('匹配分析失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取匹配详情
  async function loadMatchDetail(matchId: string) {
    try {
      loading.value = true
      error.value = ''
      const result = await getMatchDetail(matchId)
      currentMatch.value = result
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取匹配详情失败'
      console.error('获取匹配详情失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // 生成匹配反馈和学习计划
  async function generateFeedback(matchId: string) {
    try {
      loading.value = true
      error.value = ''
      const feedback = await fetch(`/match/${matchId}/feedback`).then(res => res.json())
      matchFeedback.value = feedback
      return feedback
    } catch (err: any) {
      error.value = err.response?.data?.detail || '生成反馈失败'
      console.error('生成反馈失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取匹配等级（优秀/良好/一般/较差）
  const getMatchLevel = (score: number) => {
    if (score >= 90) return { level: '优秀', color: '#10b981', text: 'text-green-600' }
    if (score >= 70) return { level: '良好', color: '#3b82f6', text: 'text-blue-600' }
    if (score >= 50) return { level: '一般', color: '#f59e0b', text: 'text-yellow-600' }
    return { level: '较差', color: '#ef4444', text: 'text-red-600' }
  }

  // 获取差距项的严重程度
  const getGapSeverity = (severity: string) => {
    switch (severity) {
      case 'high':
        return { level: '高', color: '#ef4444', text: 'text-red-600' }
      case 'medium':
        return { level: '中', color: '#f59e0b', text: 'text-yellow-600' }
      case 'low':
        return { level: '低', color: '#10b981', text: 'text-green-600' }
      default:
        return { level: '中', color: '#f59e0b', text: 'text-yellow-600' }
    }
  }

  // 获取建议的优先级
  const getRecommendationPriority = (priority: string) => {
    switch (priority) {
      case 'high':
        return { level: '高', color: '#ef4444', text: 'text-red-600' }
      case 'medium':
        return { level: '中', color: '#f59e0b', text: 'text-yellow-600' }
      case 'low':
        return { level: '低', color: '#10b981', text: 'text-green-600' }
      default:
        return { level: '中', color: '#f59e0b', text: 'text-yellow-600' }
    }
  }

  // 计算完成进度
  const calculateProgress = (match: MatchAnalysisResult) => {
    if (!match) return 0

    const totalGaps = match.gaps.length
    const totalRecommendations = match.recommendations.length

    if (totalGaps === 0 && totalRecommendations === 0) return 100

    // 计算高优先级差距和建议的数量
    const highPriorityGaps = match.gaps.filter(gap => gap.severity === 'high').length
    const highPriorityRecommendations = match.recommendations.filter(rec => rec.priority === 'high').length

    // 假设完成情况（简化处理）
    const completedGaps = Math.max(0, totalGaps - highPriorityGaps)
    const completedRecommendations = Math.max(0, totalRecommendations - highPriorityRecommendations)

    return Math.round(((completedGaps + completedRecommendations) / (totalGaps + totalRecommendations)) * 100)
  }

  // 计算各维度匹配度
  const getMatchBreakdown = (match: MatchAnalysisResult) => {
    return {
      skill: {
        score: match.skill_match,
        label: '技能匹配',
        weight: 0.5,
        color: '#8b5cf6'
      },
      experience: {
        score: match.experience_match,
        label: '经验匹配',
        weight: 0.3,
        color: '#06b6d4'
      },
      education: {
        score: match.education_match,
        label: '教育匹配',
        weight: 0.2,
        color: '#10b981'
      }
    }
  }

  return {
    // 状态
    matches,
    currentMatch,
    matchFeedback,
    loading,
    error,

    // 计算属性
    hasMatches: computed(() => matches.value.length > 0),
    currentMatchLevel: computed(() => {
      if (!currentMatch.value) return null
      return getMatchLevel(currentMatch.value.overall_score)
    }),
    matchProgress: computed(() => {
      if (!currentMatch.value) return 0
      return calculateProgress(currentMatch.value)
    }),
    matchBreakdown: computed(() => {
      if (!currentMatch.value) return null
      return getMatchBreakdown(currentMatch.value)
    }),

    // 方法
    fetchMatches,
    analyzeMatchData,
    loadMatchDetail,
    generateFeedback,
    getMatchLevel,
    getGapSeverity,
    getRecommendationPriority
  }
})