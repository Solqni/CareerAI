<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useResumeStore } from '@/stores/resume'
import {
  deleteResume,
  getResumes,
  updateResumeProfile,
  type ResumeListItem
} from '@/api/resume'

const router = useRouter()
const resumeStore = useResumeStore()

const resumeText = ref('')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const result = ref<any>(null)
const fileName = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const editing = ref(false)
const showDetailed = ref(false)

// 从 profile 构造展示数据：优先使用 parsed_json 全量解析结果，回退到合并字段
function buildResult() {
  const profile = resumeStore.profile
  if (!profile) return null
  const pj = profile.parsed_json
  if (pj && (pj.skills?.length || pj.experiences?.length)) {
    return {
      name: pj.name || profile.username,
      email: pj.email || profile.email,
      phone: pj.phone || profile.phone,
      summary: pj.summary || profile.summary,
      skills: pj.skills,
      experiences: pj.experiences,
      education: pj.education,
      certificates: pj.certificates || [],
      awards: pj.awards || [],
      languages: pj.languages || [],
      job_intention: pj.job_intention || null,
      highlights: pj.highlights || [],
      analysis: pj.analysis || null
    }
  }
  return {
    name: profile.username,
    email: profile.email,
    phone: profile.phone,
    summary: profile.summary,
    skills: profile.skills,
    experiences: profile.experiences_details,
    education: profile.education_details
  }
}

async function handleParse() {
  if (!resumeText.value.trim()) return
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    await resumeStore.parseResume(resumeText.value)
    result.value = buildResult()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || e.message || '解析失败'
  } finally {
    loading.value = false
  }
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    fileName.value = target.files[0].name
    handleUpload(target.files[0])
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    fileName.value = e.dataTransfer.files[0].name
    handleUpload(e.dataTransfer.files[0])
  }
}

async function handleUpload(file: File) {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    await resumeStore.uploadFile(file)
    result.value = buildResult()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || e.message || '上传解析失败'
  } finally {
    loading.value = false
  }
}

const proficiencyLabel = (p: number) => ['初学', '了解', '熟悉', '熟练', '精通'][Math.min(p - 1, 4)] || '熟悉'
const typeLabel = (t: string) => ({ work: '工作经历', internship: '实习经历', project: '项目经历' }[t] || t)

// 处理更新信息：保存编辑的基本信息到最新简历（PUT /resume/profile）
async function handleUpdate() {
  if (!result.value) return
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await updateResumeProfile({
      name: result.value.name || undefined,
      email: result.value.email || undefined,
      phone: result.value.phone || undefined,
      summary: result.value.summary || undefined,
    })
    await resumeStore.fetchProfile()
    result.value = buildResult()
    editing.value = false
    successMsg.value = '简历信息已保存'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || e.message || '更新失败'
  } finally {
    loading.value = false
  }
}

// 我的简历：历史列表管理（删除错传/过期简历，避免脏数据堆积）
const resumeList = ref<ResumeListItem[]>([])
const listLoading = ref(false)
const deletingId = ref<number | null>(null)

async function fetchResumeList() {
  listLoading.value = true
  try {
    resumeList.value = await getResumes()
  } catch (err: any) {
    console.error('获取简历列表失败:', err)
  } finally {
    listLoading.value = false
  }
}

async function handleDeleteResume(item: ResumeListItem) {
  if (deletingId.value) return
  if (!window.confirm(`确定删除简历「${item.name || '未命名'}」吗？该操作不可恢复。`)) return
  deletingId.value = item.id
  try {
    await deleteResume(item.id)
    await fetchResumeList()
    // 若删除的是最新简历，刷新画像展示
    await resumeStore.fetchProfile()
    result.value = buildResult()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '删除失败'
    console.error('删除简历失败:', e)
  } finally {
    deletingId.value = null
  }
}

function fmtDate(d: string) {
  return new Date(d).toLocaleString('zh-CN', { hour12: false })
}

// 初始化时获取已保存的简历数据
onMounted(async () => {
  try {
    await resumeStore.fetchProfile()
    result.value = buildResult()
  } catch (err) {
    console.error('获取简历信息失败:', err)
  }
  fetchResumeList()
})
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
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM8 13h8M8 17h8M8 9h2" />
        </svg>
      </div>
      <div>
        <h2>简历解析</h2>
        <p>上传 PDF/Word 简历，或直接粘贴文本，AI 自动提取技能、经历与教育背景</p>
      </div>
    </div>

    <!-- 上传区域 -->
    <div
      class="upload-zone anim-fade-up anim-delay-1"
      @click="fileInput?.click()"
      @dragover.prevent
      @drop="onDrop"
    >
      <input ref="fileInput" type="file" accept=".pdf,.docx,.doc,.md,.txt" hidden @change="onFileChange" />
      <div class="upload-inner">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
        <p>{{ fileName || '拖拽文件到此处，或' }} <span class="link">点击上传</span></p>
        <small>支持 PDF / Word / Markdown / TXT 格式，文件大小不超过 10MB</small>
      </div>
    </div>

    <div class="divider anim-fade-up anim-delay-2"><span>或粘贴简历文本</span></div>

    <div v-if="!editing && result" class="result-section">
      <div class="section-actions">
        <button class="btn-outline" @click="editing = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          修改信息
        </button>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-if="editing" class="edit-section anim-fade-up">
      <h4>编辑简历内容</h4>
      <div class="edit-form">
        <div class="form-group">
          <label>基本信息</label>
          <div class="info-edit">
            <input v-model="result.name" placeholder="请输入姓名" />
            <input v-model="result.email" placeholder="请输入邮箱" />
            <input v-model="result.phone" placeholder="请输入电话" />
          </div>
        </div>

        <div class="form-group">
          <label>个人概述</label>
          <textarea v-model="result.summary" placeholder="请输入个人概述"></textarea>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" @click="editing = false">取消</button>
          <button class="btn" @click="handleUpdate">
            <span v-if="loading" class="spinner"></span>
            保存修改
          </button>
        </div>
      </div>
    </div>

    <div v-else class="editor-wrap anim-fade-up anim-delay-2">
      <textarea v-model="resumeText" placeholder="在此粘贴你的简历内容...&#10;&#10;例如：姓名、教育背景、项目经历、技能清单等"></textarea>
      <div class="editor-meta">
        <span>{{ resumeText.length }} 字</span>
        <button class="btn" :disabled="loading || !resumeText.trim()" @click="handleParse">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'AI 解析中...' : '开始解析' }}
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg anim-fade-up">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ errorMsg }}
    </div>

    <!-- 成功提示 -->
    <div v-if="successMsg" class="success-msg anim-fade-up">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      {{ successMsg }}
    </div>

    <!-- 解析结果 -->
    <div v-if="result" class="result-card anim-fade-up">
      <div class="result-header">
        <h3>简历信息</h3>
        <div class="header-actions">
          <div class="view-toggle">
            <button class="toggle-btn" :class="{ active: !showDetailed }" @click="showDetailed = false">
              简化视图
            </button>
            <button class="toggle-btn" :class="{ active: showDetailed }" @click="showDetailed = true">
              详细视图
            </button>
          </div>
          <button v-if="!editing" class="edit-btn" @click="editing = true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            编辑
          </button>
        </div>
      </div>

      <!-- 基本信息（两种视图均显示，含求职意向） -->
      <div v-if="result.name || result.email || result.phone || result.job_intention" class="result-section">
        <h4>基本信息</h4>
        <div class="info-row">
          <span v-if="result.name"><strong>姓名：</strong>{{ result.name }}</span>
          <span v-if="result.email"><strong>邮箱：</strong>{{ result.email }}</span>
          <span v-if="result.phone"><strong>电话：</strong>{{ result.phone }}</span>
        </div>
        <div v-if="result.job_intention" class="intention-row">
          <strong>求职意向：</strong>{{ result.job_intention }}
        </div>
      </div>

      <!-- AI 分析：简化视图显示亮点，详细视图补充优势/待提升/综合评价 -->
      <div v-if="result.highlights?.length || result.analysis" class="result-section analysis-card">
        <div class="analysis-header">
          <h4>AI 分析</h4>
          <span v-if="result.analysis?.estimated_years" class="years-chip">{{ result.analysis.estimated_years }}</span>
        </div>

        <div v-if="result.highlights?.length" class="analysis-block">
          <div class="block-title">简历亮点</div>
          <ul class="highlight-list">
            <li v-for="(h, i) in (showDetailed ? result.highlights : result.highlights.slice(0, 3))" :key="i">{{ h }}</li>
          </ul>
          <button v-if="!showDetailed && result.highlights.length > 3" class="expand-hint" @click="showDetailed = true">
            查看全部 {{ result.highlights.length }} 条亮点 →
          </button>
        </div>

        <template v-if="showDetailed && result.analysis">
          <div v-if="result.analysis.strengths?.length || result.analysis.weaknesses?.length" class="sw-grid">
            <div v-if="result.analysis.strengths?.length" class="sw-col strengths">
              <div class="block-title">核心优势</div>
              <ul><li v-for="(s, i) in result.analysis.strengths" :key="i">{{ s }}</li></ul>
            </div>
            <div v-if="result.analysis.weaknesses?.length" class="sw-col weaknesses">
              <div class="block-title">待提升</div>
              <ul><li v-for="(w, i) in result.analysis.weaknesses" :key="i">{{ w }}</li></ul>
            </div>
          </div>
          <p v-if="result.analysis.career_summary" class="career-summary">{{ result.analysis.career_summary }}</p>
        </template>
      </div>

      <!-- 个人概述：简化视图两行截断，详细视图完整显示 -->
      <div v-if="result.summary" class="result-section">
        <h4>个人概述</h4>
        <p class="summary-text" :class="{ clamp: !showDetailed }">{{ result.summary }}</p>
        <button v-if="!showDetailed && result.summary.length > 60" class="expand-hint" @click="showDetailed = true">
          展开完整概述 →
        </button>
      </div>

      <!-- 技能：简化视图只显示前 8 项技能名，详细视图带分类与熟练度 -->
      <div v-if="result.skills?.length" class="result-section">
        <h4>技能清单</h4>
        <div class="skill-tags">
          <template v-if="showDetailed">
            <span v-for="skill in result.skills" :key="skill.skill_name" class="skill-tag">
              {{ skill.skill_name }}
              <small>
                <em v-if="skill.category" class="skill-cat">{{ skill.category }}</em>
                {{ proficiencyLabel(skill.proficiency) }}
              </small>
            </span>
          </template>
          <template v-else>
            <span v-for="skill in result.skills.slice(0, 8)" :key="skill.skill_name" class="skill-tag">
              {{ skill.skill_name }}
            </span>
            <span v-if="result.skills.length > 8" class="more-tag" @click="showDetailed = true">
              +{{ result.skills.length - 8 }} 项
            </span>
          </template>
        </div>
      </div>

      <!-- 经历：简化视图只列标题，详细视图含描述与时间 -->
      <div v-if="result.experiences?.length" class="result-section">
        <h4>经历</h4>
        <div v-for="(exp, i) in result.experiences" :key="i" class="exp-item">
          <div class="exp-header">
            <span class="exp-type">{{ typeLabel(exp.type) }}</span>
            <strong>{{ exp.title }}</strong>
            <small v-if="showDetailed && exp.date_range">{{ exp.date_range }}</small>
          </div>
          <p v-if="showDetailed && exp.description" class="exp-desc">{{ exp.description }}</p>
        </div>
      </div>

      <!-- 教育：详细视图额外显示时间段 -->
      <div v-if="result.education?.length" class="result-section">
        <h4>教育背景</h4>
        <div v-for="(edu, i) in result.education" :key="i" class="edu-item">
          <strong>{{ edu.school }}</strong>
          <span>{{ edu.degree }} · {{ edu.major }}</span>
          <small v-if="showDetailed && edu.date_range">{{ edu.date_range }}</small>
        </div>
      </div>

      <!-- 证书与奖项（详细视图） -->
      <div v-if="showDetailed && (result.certificates?.length || result.awards?.length)" class="result-section">
        <h4>证书与奖项</h4>
        <div v-if="result.certificates?.length" class="cert-tags">
          <span v-for="(c, i) in result.certificates" :key="'c' + i" class="cert-tag">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>
            {{ c }}
          </span>
        </div>
        <ul v-if="result.awards?.length" class="award-list">
          <li v-for="(a, i) in result.awards" :key="'a' + i">{{ a }}</li>
        </ul>
      </div>

      <!-- 语言能力（详细视图） -->
      <div v-if="showDetailed && result.languages?.length" class="result-section">
        <h4>语言能力</h4>
        <div class="cert-tags">
          <span v-for="(l, i) in result.languages" :key="i" class="cert-tag lang">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            {{ l }}
          </span>
        </div>
      </div>

      <!-- 下一步导航：简历解析完成后，引导进入岗位分析 -->
      <div v-if="result" class="next-step anim-fade-up">
        <div class="next-step-card">
          <div class="next-step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
          </div>
          <div class="next-step-info">
            <strong>下一步：分析目标岗位</strong>
            <p>查看岗位 JD 要求，对比你的技能差距</p>
          </div>
          <button class="btn btn-outline" @click="router.push('/jobs')">
            前往岗位分析
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 我的简历：历史列表管理 -->
    <div class="result-card anim-fade-up">
      <div class="result-header">
        <h3>我的简历</h3>
      </div>
      <div v-if="listLoading" class="study-empty">加载中...</div>
      <div v-else-if="!resumeList.length" class="study-empty">暂无历史简历，上传或粘贴解析后会在此列出</div>
      <ul v-else class="resume-list">
        <li v-for="(item, idx) in resumeList" :key="item.id" class="resume-item">
          <div class="resume-item-info">
            <strong>{{ item.name || '未命名简历' }}</strong>
            <small>{{ fmtDate(item.created_at) }}</small>
          </div>
          <div class="resume-item-actions">
            <span v-if="idx === 0" class="resume-badge">最新</span>
            <button
              class="resume-delete"
              :disabled="deletingId === item.id"
              @click="handleDeleteResume(item)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              {{ deletingId === item.id ? '删除中...' : '删除' }}
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
  background: linear-gradient(-45deg, #eef2ff, #f3e8ff, #e0f2fe, #f0fdf4);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.page-blob {
  position: fixed; border-radius: 50%; filter: blur(70px); z-index: -1;
  animation: float 8s ease-in-out infinite;
}
.blob-a { width: 300px; height: 300px; background: #667eea; opacity: 0.12; top: -60px; left: -40px; }
.blob-b { width: 250px; height: 250px; background: #f093fb; opacity: 0.1; bottom: -50px; right: -30px; animation-delay: -4s; }

.page-inner { padding: 2rem; max-width: 820px; margin: 0 auto; }
.page-back { margin-bottom: 1.2rem; }

.page-header { display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.8rem; }
.header-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
  animation: pulse 3.5s ease-in-out infinite;
}
.header-icon svg { width: 28px; height: 28px; }
.page-header h2 { font-size: 1.5rem; color: #1a202c; }
.page-header p { font-size: 0.9rem; color: #718096; margin-top: 0.25rem; }

/* 上传区 */
.upload-zone {
  border: 2px dashed rgba(102,126,234,0.35);
  border-radius: 16px;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  cursor: pointer;
}
.upload-zone:hover {
  border-color: var(--primary);
  background: rgba(255,255,255,0.8);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(102,126,234,0.12);
}
.upload-inner { padding: 2.4rem; text-align: center; color: #718096; }
.upload-inner svg {
  width: 44px; height: 44px;
  color: #a5b4fc;
  margin-bottom: 0.7rem;
  animation: float 3.5s ease-in-out infinite;
}
.upload-inner p { font-size: 0.95rem; color: #4a5568; }
.upload-inner .link { color: var(--primary); font-weight: 600; }
.upload-inner small { display: block; margin-top: 0.4rem; font-size: 0.78rem; color: #a0aec0; }

/* 分隔线 */
.divider {
  display: flex; align-items: center; gap: 1rem;
  margin: 1.6rem 0;
  color: #a0aec0;
  font-size: 0.82rem;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

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
  border-color: var(--primary);
  background: rgba(255,255,255,0.85);
  box-shadow: 0 0 0 4px rgba(102,126,234,0.1);
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
  background: linear-gradient(135deg, var(--primary), var(--secondary));
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
.btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(102,126,234,0.35); }
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

/* 成功提示 */
.success-msg {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 1rem 1.2rem;
  margin-top: 1.2rem;
  background: #f0fff4;
  border: 1px solid #c6f6d5;
  border-radius: 12px;
  color: #2f855a;
  font-size: 0.9rem;
}
.success-msg svg { width: 18px; height: 18px; flex-shrink: 0; }

/* 我的简历列表 */
.study-empty { color: #a0aec0; font-size: 0.9rem; text-align: center; padding: 1.2rem 0; }
.resume-list { list-style: none; margin: 0; padding: 0; }
.resume-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.9rem 0.2rem;
  border-bottom: 1px solid #edf2f7;
}
.resume-item:last-child { border-bottom: none; }
.resume-item-info { display: flex; flex-direction: column; gap: 0.2rem; }
.resume-item-info strong { color: #1a202c; font-size: 0.95rem; }
.resume-item-info small { color: #a0aec0; font-size: 0.8rem; }
.resume-item-actions { display: flex; align-items: center; gap: 0.7rem; }
.resume-badge {
  font-size: 0.75rem; color: #4c51bf; background: #ebf4ff;
  border: 1px solid #c3dafe; border-radius: 999px; padding: 0.1rem 0.6rem;
}
.resume-delete {
  display: inline-flex; align-items: center; gap: 0.3rem;
  background: none; border: 1px solid #fed7d7; border-radius: 8px;
  color: #e53e3e; font-size: 0.82rem; padding: 0.35rem 0.7rem; cursor: pointer;
  transition: all 0.2s;
}
.resume-delete svg { width: 14px; height: 14px; }
.resume-delete:hover:not(:disabled) { background: #fff5f5; }
.resume-delete:disabled { opacity: 0.5; cursor: not-allowed; }

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
.result-section { margin-bottom: 1.6rem; }
.result-section h4 {
  font-size: 0.95rem; color: #4a5568; margin-bottom: 0.6rem;
  display: flex; align-items: center; gap: 0.4rem;
}
.result-section h4::before {
  content: ''; width: 3px; height: 16px; border-radius: 2px;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.info-row { display: flex; flex-wrap: wrap; gap: 1.5rem; font-size: 0.9rem; color: #2d3748; }
.summary-text { font-size: 0.9rem; color: #4a5568; line-height: 1.7; }

/* 技能标签 */
.skill-tags { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.skill-tag {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.4rem 0.9rem;
  background: linear-gradient(135deg, #f3f4ff, #fbfbff);
  border: 1px solid #c3c9f5;
  border-radius: 8px;
  font-size: 0.85rem; color: #4a5568;
  transition: transform 0.2s ease;
}
.skill-tag:hover { transform: translateY(-2px); }
.skill-tag small { color: #a5b4fc; font-size: 0.72rem; }

/* 经历 */
.exp-item {
  padding: 0.9rem 1rem;
  background: #f7f8fc;
  border-radius: 10px;
  margin-bottom: 0.6rem;
}
.exp-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.3rem; }
.exp-type {
  font-size: 0.72rem; padding: 0.15rem 0.5rem;
  background: #667eea; color: #fff; border-radius: 4px; white-space: nowrap;
}
.exp-header strong { font-size: 0.9rem; color: #1a202c; }
.exp-header small { font-size: 0.78rem; color: #a0aec0; margin-left: auto; }
.exp-desc { font-size: 0.85rem; color: #718096; line-height: 1.6; }

/* 教育 */
.edu-item {
  display: flex; align-items: center; gap: 0.8rem; flex-wrap: wrap;
  padding: 0.7rem 1rem;
  background: #f7f8fc; border-radius: 10px; margin-bottom: 0.5rem;
  font-size: 0.88rem; color: #4a5568;
}
.edu-item strong { color: #1a202c; }
.edu-item small { color: #a0aec0; margin-left: auto; }

/* 下一步导航 */
.next-step { margin-top: 1.8rem; }
.next-step-card {
  display: flex; align-items: center; gap: 1rem;
  padding: 1.2rem 1.4rem;
  background: linear-gradient(135deg, #f3e8ff, #faf5ff);
  border: 1px solid #e9d8fd;
  border-radius: 14px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.next-step-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(118,75,162,0.12); }
.next-step-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #764ba2, #f093fb);
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
  color: #764ba2;
  border: 1.5px solid #764ba2;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex; align-items: center; gap: 0.4rem;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.btn-outline:hover { background: #764ba2; color: #fff; }
.btn-outline svg { width: 16px; height: 16px; }
/* 编辑模式样式 */
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #edf2f7;
}
.result-header h3 { font-size: 1.2rem; color: #1a202c; }
.edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.edit-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(102,126,234,0.3); }

.section-actions {
  margin-bottom: 1rem;
}

.edit-section {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.edit-section h4 {
  font-size: 1rem;
  color: #2d3748;
  margin-bottom: 1rem;
}
.edit-form .form-group {
  margin-bottom: 1.2rem;
}
.edit-form label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 0.5rem;
}
.info-edit {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.8rem;
}
.info-edit input {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: border-color 0.2s ease;
}
.info-edit input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}
.edit-form textarea {
  width: 100%;
  min-height: 100px;
  padding: 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  resize: vertical;
  transition: border-color 0.2s ease;
}
.edit-form textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}
.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}
.btn-secondary {
  padding: 0.7rem 1.5rem;
  background: #e2e8f0;
  color: #4a5568;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-secondary:hover { background: #cbd5e0; }

/* 视图切换 */
.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  background: #f8fafc;
  padding: 0.5rem;
  border-radius: 12px;
  width: fit-content;
}

.toggle-btn {
  padding: 0.5rem 1.2rem;
  background: transparent;
  color: #718096;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #e2e8f0;
  color: #4a5568;
}

.toggle-btn.active {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

/* 简化视图下概述两行截断 */
.summary-text.clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.expand-hint {
  margin-top: 0.4rem;
  padding: 0;
  background: none;
  border: none;
  color: #667eea;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
}
.expand-hint:hover { text-decoration: underline; }

/* 技能"更多"标签 */
.more-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.9rem;
  background: #f3f4ff;
  border: 1px dashed #a5b4fc;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #667eea;
  cursor: pointer;
  transition: background 0.2s ease;
}
.more-tag:hover { background: #e8eaff; }

/* 求职意向 */
.intention-row {
  margin-top: 0.6rem;
  padding: 0.55rem 0.9rem;
  background: #f8f7ff;
  border-left: 3px solid #667eea;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #4a5568;
}
.intention-row strong { color: #667eea; }

/* AI 分析卡 */
.analysis-card {
  background: linear-gradient(135deg, rgba(102,126,234,0.06), rgba(118,75,162,0.06));
  border: 1px solid rgba(102,126,234,0.18);
  border-radius: 12px;
}
.analysis-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.analysis-header h4 { margin-bottom: 0; }
.years-chip {
  padding: 0.15rem 0.6rem;
  background: #667eea;
  color: #fff;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.analysis-block { margin-top: 0.8rem; }
.block-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #764ba2;
  margin-bottom: 0.45rem;
}
.highlight-list {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.35rem;
}
.highlight-list li {
  font-size: 0.88rem;
  color: #2d3748;
  line-height: 1.55;
}
.sw-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.9rem;
  margin-top: 0.9rem;
}
.sw-col {
  padding: 0.8rem 0.9rem;
  border-radius: 10px;
}
.sw-col ul {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.3rem;
}
.sw-col li { font-size: 0.86rem; line-height: 1.5; }
.sw-col.strengths { background: rgba(72,187,120,0.08); border: 1px solid rgba(72,187,120,0.2); }
.sw-col.strengths .block-title { color: #2f855a; }
.sw-col.strengths li { color: #22543d; }
.sw-col.weaknesses { background: rgba(237,137,54,0.08); border: 1px solid rgba(237,137,54,0.2); }
.sw-col.weaknesses .block-title { color: #c05621; }
.sw-col.weaknesses li { color: #7b341e; }
.career-summary {
  margin: 0.9rem 0 0;
  padding: 0.7rem 0.9rem;
  background: rgba(255,255,255,0.7);
  border-radius: 8px;
  font-size: 0.88rem;
  line-height: 1.6;
  color: #4a5568;
}
.skill-cat {
  font-style: normal;
  margin-right: 0.35rem;
  padding: 0.05rem 0.4rem;
  background: #edf2f7;
  border-radius: 4px;
  font-size: 0.68rem;
  color: #718096;
}

/* 证书与语言 */
.cert-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.cert-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.8rem;
  background: #f0fff4;
  border: 1px solid #9ae6b4;
  border-radius: 8px;
  font-size: 0.84rem;
  color: #22543d;
}
.cert-tag svg { width: 14px; height: 14px; flex-shrink: 0; }
.cert-tag.lang { background: #ebf8ff; border-color: #90cdf4; color: #2a4365; }
.award-list {
  margin: 0.6rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.3rem;
}
.award-list li { font-size: 0.86rem; color: #2d3748; line-height: 1.5; }
</style>
