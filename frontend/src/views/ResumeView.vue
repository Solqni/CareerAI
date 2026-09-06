<script setup lang="ts">
import { ref } from 'vue'

const resumeText = ref('')
const loading = ref(false)

async function handleParse() {
  if (!resumeText.value.trim()) return
  loading.value = true
  setTimeout(() => { loading.value = false; alert('简历解析占位：请接入后端 API') }, 800)
}
</script>

<template>
  <div class="page">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>
    <div class="page-inner">
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
    <div class="upload-zone anim-fade-up anim-delay-1">
      <div class="upload-inner">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
        <p>拖拽文件到此处，或 <span class="link">点击上传</span></p>
        <small>支持 PDF / Word 格式，文件大小不超过 10MB</small>
      </div>
    </div>

    <div class="divider anim-fade-up anim-delay-2"><span>或粘贴简历文本</span></div>

    <div class="editor-wrap anim-fade-up anim-delay-2">
      <textarea v-model="resumeText" placeholder="在此粘贴你的简历内容...&#10;&#10;例如：姓名、教育背景、项目经历、技能清单等"></textarea>
      <div class="editor-meta">
        <span>{{ resumeText.length }} 字</span>
        <button class="btn" :disabled="loading || !resumeText.trim()" @click="handleParse">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'AI 解析中...' : '开始解析' }}
        </button>
      </div>
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
</style>
