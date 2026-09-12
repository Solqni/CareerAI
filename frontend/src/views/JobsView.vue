<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useJobStore } from '@/stores/job'
import { getJob } from '@/api/job'

const router = useRouter()
const jobStore = useJobStore()

const jdText = ref('')
const loading = ref(false)
const errorMsg = ref('')
const result = ref<any>(null)
const editing = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const imageLoading = ref(false)
const imageName = ref('')
const imagePreview = ref('')

// 我的岗位：列表管理（删除错析/过期岗位，避免下拉脏数据堆积）
const deletingJobId = ref<number | null>(null)

function jobTitle(job: any) {
  return job?.position_title || job?.parsed_json?.position_title || `岗位 #${job?.id}`
}

function jobCompany(job: any) {
  return job?.parsed_json?.company || ''
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

async function handleDeleteJob(job: any) {
  if (deletingJobId.value) return
  if (!window.confirm(`确定删除岗位「${jobTitle(job)}」吗？其关联的匹配报告与学习计划将一并删除，该操作不可恢复。`)) return
  deletingJobId.value = job.id
  try {
    await jobStore.deleteJob(job.id)
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '删除失败'
    console.error('删除岗位失败:', e)
  } finally {
    deletingJobId.value = null
  }
}

// 双击岗位行：加载并展示该岗位的分析详情（共享岗位也可查看）
const detailLoadingId = ref<number | null>(null)

async function showJobDetail(job: any) {
  if (detailLoadingId.value) return
  detailLoadingId.value = job.id
  errorMsg.value = ''
  try {
    const { data: detail } = await getJob(job.id)
    jobStore.currentJob = detail
    result.value = detail.parsed_json
    editing.value = false
    await nextTick()
    document.querySelector('.result-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '加载岗位详情失败'
    console.error('加载岗位详情失败:', e)
  } finally {
    detailLoadingId.value = null
  }
}

// 初始化时获取已保存的岗位
onMounted(async () => {
  try {
    await jobStore.fetchJobs()
    // 如果有最近的岗位分析，显示它
    if (jobStore.currentJob) {
      result.value = jobStore.currentJob.parsed_json
      jdText.value = jobStore.currentJob.jd_text
    }
  } catch (err) {
    console.error('获取岗位信息失败:', err)
  }
})

async function handleParse() {
  if (!jdText.value.trim()) return
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    await jobStore.parseJob(jdText.value)
    result.value = jobStore.currentJob?.parsed_json
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || e.message || '解析失败'
  } finally {
    loading.value = false
  }
}

// ===== JD 截图上传识别 =====
function onImageChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) handleImageUpload(target.files[0])
}

function onImageDrop(e: DragEvent) {
  e.preventDefault()
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  if (file.type.startsWith('image/')) {
    handleImageUpload(file)
  } else {
    errorMsg.value = '请上传图片文件（JPG / PNG / WebP / BMP）'
  }
}

async function handleImageUpload(file: File) {
  imageLoading.value = true
  errorMsg.value = ''
  result.value = null
  imageName.value = file.name
  imagePreview.value = URL.createObjectURL(file)
  try {
    await jobStore.parseImageJob(file)
    if (jobStore.currentJob) {
      result.value = jobStore.currentJob.parsed_json
      jdText.value = jobStore.currentJob.jd_text
    }
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || e.message || '图片识别失败'
  } finally {
    imageLoading.value = false
  }
}

function clearImage() {
  imageName.value = ''
  imagePreview.value = ''
  if (imageInput.value) imageInput.value.value = ''
}
</script>

<template>
  <div class="page">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>
    <div class="page-inner">
    <BackButton class="page-back" />
    <div class="page-header anim-fade-up">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        </svg>
      </div>
      <div>
        <h2>岗位分析</h2>
        <p>上传 JD 截图或粘贴文本，AI 提取岗位职责、必备技能、加分项与学历要求</p>
      </div>
    </div>

    <div class="tips anim-fade-up anim-delay-1">
      <div class="tip"><strong>岗位职责</strong>提取工作内容要点</div>
      <div class="tip"><strong>必备技能</strong>标注硬性技术要求</div>
      <div class="tip"><strong>加分项</strong>识别优先条件</div>
    </div>

    <!-- JD 截图上传 -->
    <div v-if="!imagePreview" class="image-upload-zone anim-fade-up anim-delay-1"
      @click="imageInput?.click()"
      @dragover.prevent
      @drop="onImageDrop"
    >
      <input ref="imageInput" type="file" accept=".jpg,.jpeg,.png,.webp,.bmp" hidden @change="onImageChange" />
      <div class="image-upload-inner">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
        <p>上传 JD 截图（招聘 App / 网站均可），AI 高精度识别图中文字并解析岗位要求；拖拽图片到此处，或 <span class="link">点击上传</span></p>
        <small>支持 JPG / PNG / WebP / BMP，大小不超过 10MB，识别后自动解析</small>
      </div>
    </div>

    <div v-else class="image-preview-card anim-fade-up anim-delay-1">
      <img :src="imagePreview" alt="JD 截图预览" />
      <div class="image-preview-info">
        <strong>{{ imageName }}</strong>
        <p v-if="imageLoading" class="recognizing"><span class="spinner dark"></span>AI 正在识别图片中的职位信息...</p>
        <p v-else>识别完成，JD 文字已填入下方文本框</p>
      </div>
      <button class="remove-image-btn" :disabled="imageLoading" title="移除图片" @click="clearImage">✕</button>
    </div>

    <div class="divider anim-fade-up anim-delay-2"><span>或直接粘贴 JD 文本</span></div>

    <div class="editor-wrap anim-fade-up anim-delay-2">
      <textarea v-model="jdText" placeholder="在此粘贴目标岗位的 JD 描述...&#10;&#10;例如：岗位职责、任职要求、薪资范围等"></textarea>
      <div class="editor-meta">
        <span>{{ jdText.length }} 字 · JD 过短可能影响解析质量</span>
        <button class="btn" :disabled="loading || imageLoading || !jdText.trim()" @click="handleParse">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'AI 解析中...' : '解析 JD' }}
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg anim-fade-up">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ errorMsg }}
    </div>

    <!-- 解析结果 -->
    <div v-if="result" class="result-card anim-fade-up">
      <div class="result-header">
        <h3>岗位分析结果</h3>
        <span class="save-note">解析完成已自动保存到我的岗位</span>
      </div>

      <!-- 岗位名称 -->
      <div v-if="result.position_title" class="result-section">
        <h4>岗位名称</h4>
        <p class="position-title">{{ result.position_title }}</p>
      </div>

      <!-- 岗位概述 -->
      <div v-if="result.summary" class="result-section">
        <h4>岗位概述</h4>
        <p class="summary-text">{{ result.summary }}</p>
      </div>

      <!-- 岗位职责 -->
      <div v-if="result.responsibilities?.length" class="result-section">
        <h4>岗位职责</h4>
        <ul class="resp-list">
          <li v-for="(r, i) in result.responsibilities" :key="i">{{ r }}</li>
        </ul>
      </div>

      <!-- 技能要求 -->
      <div v-if="result.required_skills?.length" class="result-section">
        <h4>技能要求</h4>
        <div class="skill-groups">
          <div class="skill-group">
            <span class="group-label must">必备</span>
            <div class="skill-tags">
              <span v-for="s in result.required_skills.filter((x: any) => x.requirement_level !== 'plus')" :key="s.skill_name" class="skill-tag must">
                {{ s.skill_name }}
                <small v-if="s.category">{{ s.category }}</small>
              </span>
            </div>
          </div>
          <div v-if="result.required_skills.some((x: any) => x.requirement_level === 'plus')" class="skill-group">
            <span class="group-label plus">加分</span>
            <div class="skill-tags">
              <span v-for="s in result.required_skills.filter((x: any) => x.requirement_level === 'plus')" :key="s.skill_name" class="skill-tag plus">
                {{ s.skill_name }}
                <small v-if="s.category">{{ s.category }}</small>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 学历与经验要求 -->
      <div v-if="result.education_requirement || result.experience_requirement" class="result-section">
        <h4>任职要求</h4>
        <div class="req-row">
          <span v-if="result.education_requirement"><strong>学历：</strong>{{ result.education_requirement }}</span>
          <span v-if="result.experience_requirement"><strong>经验：</strong>{{ result.experience_requirement }}</span>
        </div>
      </div>

      <!-- 下一步导航：岗位分析完成后，引导进入能力匹配 -->
      <div v-if="result" class="next-step anim-fade-up">
        <div class="next-step-card">
          <div class="next-step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div class="next-step-info">
            <strong>下一步：能力匹配</strong>
            <p>对比简历技能与岗位要求，生成差距报告</p>
          </div>
          <button class="btn btn-outline" @click="router.push({ path: '/match/new', query: jobStore.currentJob?.id ? { jobId: String(jobStore.currentJob.id) } : {} })">
            前往能力匹配
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 我的岗位：列表管理 -->
    <div class="result-card anim-fade-up">
      <div class="result-header">
        <h3>我的岗位</h3>
        <span class="job-hint">双击岗位可查看分析详情</span>
      </div>
      <div v-if="jobStore.loading" class="list-empty">加载中...</div>
      <div v-else-if="!jobStore.jobs.length" class="list-empty">暂无岗位分析记录，上传 JD 或截图后会在此列出</div>
      <ul v-else class="job-list">
        <li
          v-for="job in jobStore.jobs"
          :key="job.id"
          class="job-item"
          :class="{ loading: detailLoadingId === job.id }"
          title="双击查看分析详情"
          @dblclick="showJobDetail(job)"
        >
          <div class="job-item-info">
            <strong>{{ jobTitle(job) }}<span v-if="detailLoadingId === job.id" class="spinner spinner-sm"></span></strong>
            <small>{{ [jobCompany(job), fmtDate(job.created_at)].filter(Boolean).join(' · ') }}</small>
          </div>
          <div class="job-item-actions">
            <span v-if="job.is_shared" class="job-badge">平台共享</span>
            <button
              v-else
              class="job-delete"
              :disabled="deletingJobId === job.id"
              @click="handleDeleteJob(job)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              {{ deletingJobId === job.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </li>
      </ul>
    </div>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; position: relative; overflow: hidden; }
.page-bg {
  position: fixed; inset: 0; z-index: -2;
  background: linear-gradient(-45deg, #faf5ff, #fdf2f8, #f3e8ff, #e0f2fe);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.page-blob {
  position: fixed; border-radius: 50%; filter: blur(70px); z-index: -1;
  animation: float 8s ease-in-out infinite;
}
.blob-a { width: 300px; height: 300px; background: #764ba2; opacity: 0.1; top: -60px; right: -40px; }
.blob-b { width: 250px; height: 250px; background: #f093fb; opacity: 0.1; bottom: -50px; left: -30px; animation-delay: -4s; }

.page-inner { padding: 2rem; max-width: 820px; margin: 0 auto; }
.page-back { margin-bottom: 1.2rem; }

.page-header { display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.6rem; }
.header-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #764ba2, #f093fb);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(118,75,162,0.3);
  animation: pulse 3.5s ease-in-out infinite;
}
.header-icon svg { width: 28px; height: 28px; }
.page-header h2 { font-size: 1.5rem; color: #1a202c; }
.page-header p { font-size: 0.9rem; color: #718096; margin-top: 0.25rem; }

/* JD 截图上传 */
.image-upload-zone {
  border: 2px dashed rgba(118,75,162,0.35);
  border-radius: 16px;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  cursor: pointer;
  margin-bottom: 1.4rem;
}
.image-upload-zone:hover {
  border-color: #764ba2;
  background: rgba(255,255,255,0.8);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(118,75,162,0.12);
}
.image-upload-inner { padding: 1.8rem; text-align: center; color: #718096; }
.image-upload-inner svg {
  width: 40px; height: 40px;
  color: #d8b4fe;
  margin-bottom: 0.6rem;
  animation: float 3.5s ease-in-out infinite;
}
.image-upload-inner p { font-size: 0.92rem; color: #4a5568; }
.image-upload-inner .link { color: #764ba2; font-weight: 600; }
.image-upload-inner small { display: block; margin-top: 0.4rem; font-size: 0.78rem; color: #a0aec0; }

.image-preview-card {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1.4rem;
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(118,75,162,0.25);
  border-radius: 14px;
}
.image-preview-card img {
  width: 86px; height: 64px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.image-preview-info { flex: 1; min-width: 0; }
.image-preview-info strong {
  display: block;
  font-size: 0.9rem; color: #1a202c;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.image-preview-info p { margin-top: 0.25rem; font-size: 0.8rem; color: #718096; }
.image-preview-info .recognizing { display: flex; align-items: center; gap: 0.45rem; color: #764ba2; }
.remove-image-btn {
  width: 30px; height: 30px;
  border: none;
  border-radius: 8px;
  background: #f1f5f9;
  color: #718096;
  font-size: 0.9rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.remove-image-btn:hover:not(:disabled) { background: #fed7d7; color: #c53030; }
.remove-image-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.spinner.dark {
  border: 2px solid rgba(118,75,162,0.25);
  border-top-color: #764ba2;
  width: 13px; height: 13px;
}

/* 分隔线 */
.divider {
  display: flex; align-items: center; gap: 1rem;
  margin: 0 0 1.4rem;
  color: #a0aec0;
  font-size: 0.82rem;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

/* 提示卡片 */
.tips { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.8rem; margin-bottom: 1.4rem; }
.tip {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(238,229,247,0.5);
  border-radius: 12px;
  padding: 0.8rem 1rem;
  font-size: 0.85rem;
  color: #718096;
  transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}
.tip:hover { transform: translateY(-3px); background: rgba(255,255,255,0.8); box-shadow: 0 8px 20px rgba(118,75,162,0.12); }
.tip strong { display: block; color: #764ba2; margin-bottom: 0.2rem; font-size: 0.9rem; }

/* 编辑区 */
.editor-wrap textarea {
  width: 100%;
  min-height: 260px;
  padding: 1.2rem;
  border: 1.5px solid rgba(226,232,240,0.6);
  border-radius: 14px;
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(10px);
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}
.editor-wrap textarea:focus {
  border-color: #764ba2;
  background: rgba(255,255,255,0.85);
  box-shadow: 0 0 0 4px rgba(118,75,162,0.1);
}
.editor-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  font-size: 0.85rem;
  color: #a0aec0;
}
.btn {
  padding: 0.7rem 1.8rem;
  background: linear-gradient(135deg, #764ba2, #f093fb);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: transform 0.2s ease, box-shadow 0.25s ease, opacity 0.2s ease;
}
.btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(118,75,162,0.35); }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.spinner {
  width: 15px; height: 15px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* 错误提示 */
.error-msg {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 1rem 1.2rem;
  margin-top: 1.2rem;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 12px;
  color: #c53030;
  font-size: 0.9rem;
}
.error-msg svg { width: 18px; height: 18px; flex-shrink: 0; }

/* 解析结果 */
.result-card {
  margin-top: 2rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.8rem;
}
.result-card h3 {
  font-size: 1.2rem; color: #1a202c; margin-bottom: 1.2rem;
  padding-bottom: 0.8rem; border-bottom: 1px solid #edf2f7;
}

/* 我的岗位列表 */
.job-hint { font-size: 0.78rem; color: #a0aec0; font-weight: 400; }
.list-empty { color: #a0aec0; font-size: 0.9rem; text-align: center; padding: 1.2rem 0; }
.job-list { list-style: none; margin: 0; padding: 0; }
.job-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.9rem 0.4rem;
  border-bottom: 1px solid #edf2f7;
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 8px;
}
.job-item:hover { background: #f7fafc; }
.job-item.loading { opacity: 0.55; pointer-events: none; }
.spinner-sm {
  display: inline-block; width: 12px; height: 12px;
  margin-left: 0.5rem; vertical-align: middle;
  border: 2px solid #cbd5e0; border-top-color: #764ba2; border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.job-item:last-child { border-bottom: none; }
.job-item-info { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.job-item-info strong { color: #1a202c; font-size: 0.95rem; }
.job-item-info small { color: #a0aec0; font-size: 0.8rem; }
.job-item-actions { display: flex; align-items: center; gap: 0.7rem; flex-shrink: 0; }
.job-badge {
  font-size: 0.75rem; color: #2c7a7b; background: #e6fffa;
  border: 1px solid #b2f5ea; border-radius: 999px; padding: 0.1rem 0.6rem;
}
.job-delete {
  display: inline-flex; align-items: center; gap: 0.3rem;
  background: none; border: 1px solid #fed7d7; border-radius: 8px;
  color: #e53e3e; font-size: 0.82rem; padding: 0.35rem 0.7rem; cursor: pointer;
  transition: all 0.2s;
}
.job-delete svg { width: 14px; height: 14px; }
.job-delete:hover:not(:disabled) { background: #fff5f5; }
.job-delete:disabled { opacity: 0.5; cursor: not-allowed; }
.result-section { margin-bottom: 1.6rem; }
.result-section h4 {
  font-size: 0.95rem; color: #4a5568; margin-bottom: 0.6rem;
  display: flex; align-items: center; gap: 0.4rem;
}
.result-section h4::before {
  content: ''; width: 3px; height: 16px; border-radius: 2px;
  background: linear-gradient(135deg, #764ba2, #f093fb);
}

.position-title { font-size: 1.05rem; font-weight: 600; color: #1a202c; }
.summary-text { font-size: 0.9rem; color: #4a5568; line-height: 1.7; }

/* 岗位职责 */
.resp-list { list-style: none; padding: 0; }
.resp-list li {
  position: relative;
  padding: 0.5rem 0 0.5rem 1.4rem;
  font-size: 0.88rem;
  color: #4a5568;
  line-height: 1.6;
}
.resp-list li::before {
  content: '';
  position: absolute; left: 0; top: 0.85rem;
  width: 6px; height: 6px; border-radius: 50%;
  background: #764ba2;
}

/* 技能分组 */
.skill-groups { display: flex; flex-direction: column; gap: 1rem; }
.skill-group { display: flex; align-items: flex-start; gap: 0.8rem; }
.group-label {
  flex-shrink: 0;
  font-size: 0.75rem; font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  margin-top: 0.15rem;
}
.group-label.must { background: #fed7d7; color: #c53030; }
.group-label.plus { background: #c6f6d5; color: #276749; }
.skill-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.skill-tag {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.35rem 0.8rem;
  border-radius: 8px;
  font-size: 0.85rem; color: #4a5568;
  transition: transform 0.2s ease;
}
.skill-tag.must {
  background: linear-gradient(135deg, #fff5f5, #fff0f0);
  border: 1px solid #fed7d7;
}
.skill-tag.plus {
  background: linear-gradient(135deg, #f0fff4, #e6ffed);
  border: 1px solid #c6f6d5;
}
.skill-tag:hover { transform: translateY(-2px); }
.skill-tag small { color: #a0aec0; font-size: 0.72rem; }

/* 任职要求 */
.req-row { display: flex; flex-wrap: wrap; gap: 1.5rem; font-size: 0.9rem; color: #2d3748; }
.req-row strong { color: #764ba2; }

/* 下一步导航 */
.next-step { margin-top: 1.8rem; }
.next-step-card {
  display: flex; align-items: center; gap: 1rem;
  padding: 1.2rem 1.4rem;
  background: linear-gradient(135deg, #eef2ff, #f3e8ff);
  border: 1px solid #d4d9fc;
  border-radius: 14px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.next-step-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(102,126,234,0.12); }
.next-step-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.next-step-icon svg { width: 22px; height: 22px; }
.next-step-info { flex: 1; }
.next-step-info strong { display: block; font-size: 0.95rem; color: #1a202c; margin-bottom: 0.15rem; }
.next-step-info p { font-size: 0.82rem; color: #718096; }
.btn-outline {
  padding: 0.6rem 1.2rem;
  background: transparent;
  color: #667eea;
  border: 1.5px solid #667eea;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex; align-items: center; gap: 0.4rem;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.btn-outline:hover { background: #667eea; color: #fff; }
.btn-outline svg { width: 16px; height: 16px; }

/* 保存按钮样式 */
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #edf2f7;
}
.result-header h3 { font-size: 1.2rem; color: #1a202c; }
.save-note { font-size: 0.78rem; color: #38a169; background: #f0fff4; border: 1px solid #c6f6d5; border-radius: 999px; padding: 0.2rem 0.7rem; }
</style>
