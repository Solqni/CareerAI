import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile, parseResumeText, uploadResumeFile } from '@/api/resume'

export const useResumeStore = defineStore('resume', () => {
  const profile = ref<any>(null)
  const loading = ref(false)
  const error = ref('')

  // 获取用户能力画像
  async function fetchProfile() {
    try {
      loading.value = true
      error.value = ''
      profile.value = await getProfile()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取简历信息失败'
      console.error('获取简历信息失败:', err)
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  // 解析简历文本
  async function parseResume(text: string) {
    try {
      loading.value = true
      error.value = ''
      const res = await parseResumeText(text)
      // 解析成功后重新获取用户数据
      await fetchProfile()
      return res
    } catch (err: any) {
      error.value = err.response?.data?.detail || '解析失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 上传并解析简历文件
  async function uploadFile(file: File) {
    try {
      loading.value = true
      error.value = ''
      const res = await uploadResumeFile(file)
      // 解析成功后重新获取用户数据
      await fetchProfile()
      return res
    } catch (err: any) {
      error.value = err.response?.data?.detail || '上传解析失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 添加技能
  async function addSkill(_skill: { skill_name: string; proficiency: number }) {
    try {
      loading.value = true
      error.value = ''
      // TODO: 实现添加技能的API调用
      await fetchProfile()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '添加技能失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除技能
  async function deleteSkill(_skillId: number) {
    try {
      loading.value = true
      error.value = ''
      // TODO: 实现删除技能的API调用
      await fetchProfile()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '删除技能失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    profile,
    loading,
    error,
    fetchProfile,
    parseResume,
    uploadFile,
    addSkill,
    deleteSkill
  }
})