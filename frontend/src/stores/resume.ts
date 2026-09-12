import { defineStore } from 'pinia'
import { ref } from 'vue'
import { addSkill as addSkillApi, deleteSkill as deleteSkillApi, getProfile, getResumes, parseResumeText, uploadResumeFile, type ResumeListItem } from '@/api/resume'

export const useResumeStore = defineStore('resume', () => {
  const profile = ref<any>(null)
  const resumes = ref<ResumeListItem[]>([])
  const loading = ref(false)
  const error = ref('')

  // 获取用户简历列表（匹配/优化场景的下拉数据源）
  async function fetchResumes() {
    try {
      resumes.value = await getResumes()
    } catch (err: any) {
      console.error('获取简历列表失败:', err)
      resumes.value = []
    }
  }

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

  // 添加技能（手动，POST /resume/skills）
  async function addSkill(skill: { skill_name: string; proficiency: number }) {
    try {
      loading.value = true
      error.value = ''
      await addSkillApi(skill)
      await fetchProfile()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '添加技能失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除技能（DELETE /resume/skills/{id}）
  async function deleteSkill(skillId: number) {
    try {
      loading.value = true
      error.value = ''
      await deleteSkillApi(skillId)
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
    resumes,
    loading,
    error,
    fetchResumes,
    fetchProfile,
    parseResume,
    uploadFile,
    addSkill,
    deleteSkill
  }
})