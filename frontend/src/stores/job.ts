import { defineStore } from 'pinia'
import { ref } from 'vue'
import { parseJobDescription, parseJobImage, getJobs, createJob, deleteJob as deleteJobApi, type Job } from '@/api/job'

export const useJobStore = defineStore('job', () => {
  const jobs = ref<Job[]>([])
  const currentJob = ref<Job | null>(null)
  const loading = ref(false)
  const error = ref('')

  // 获取用户的所有岗位分析
  async function fetchJobs() {
    try {
      loading.value = true
      error.value = ''
      jobs.value = await getJobs()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取岗位列表失败'
    } finally {
      loading.value = false
    }
  }

  // 解析岗位描述
  async function parseJob(jdText: string) {
    try {
      loading.value = true
      error.value = ''
      const result = await parseJobDescription(jdText)

      // 保存当前解析的岗位
      currentJob.value = {
        id: Date.now(),
        title: result.data.parsed_json.position_title || '未命名岗位',
        jd_text: jdText,
        parsed_json: result.data.parsed_json,
        created_at: new Date().toISOString()
      }

      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '解析失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 上传 JD 截图，视觉模型识别后解析
  async function parseImageJob(file: File) {
    try {
      loading.value = true
      error.value = ''
      const result = await parseJobImage(file)

      currentJob.value = {
        id: result.data.id ?? Date.now(),
        title: result.data.parsed_json?.position_title || '未命名岗位',
        jd_text: result.data.jd_text || '',
        parsed_json: result.data.parsed_json,
        created_at: result.data.created_at || new Date().toISOString()
      }

      return currentJob.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '图片识别失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 保存岗位分析结果
  async function saveJob(jobData: Partial<Job>) {
    try {
      loading.value = true
      error.value = ''

      if (currentJob.value) {
        // 更新现有岗位
        Object.assign(currentJob.value, jobData)
      } else {
        // 创建新岗位
        const newJob = await createJob(jobData)
        jobs.value.unshift(newJob)
        currentJob.value = newJob
      }

      return currentJob.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || '保存失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除岗位（真实调用后端，级联清理报告链）
  async function deleteJob(jobId: number) {
    try {
      loading.value = true
      error.value = ''
      await deleteJobApi(jobId)
      jobs.value = jobs.value.filter(j => j.id !== jobId)
      if (currentJob.value?.id === jobId) {
        currentJob.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || '删除失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    jobs,
    currentJob,
    loading,
    error,
    fetchJobs,
    parseJob,
    parseImageJob,
    saveJob,
    deleteJob
  }
})