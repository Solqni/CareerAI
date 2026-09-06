<script setup lang="ts">
import { ref } from 'vue'
import BackButton from '@/components/BackButton.vue'

const jdText = ref('')
const loading = ref(false)

async function handleParse() {
  if (!jdText.value.trim()) return
  loading.value = true
  setTimeout(() => { loading.value = false; alert('JD 解析占位：请接入后端 API') }, 800)
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
        <p>粘贴目标岗位 JD，AI 提取岗位职责、必备技能、加分项与学历要求</p>
      </div>
    </div>

    <div class="tips anim-fade-up anim-delay-1">
      <div class="tip"><strong>岗位职责</strong>提取工作内容要点</div>
      <div class="tip"><strong>必备技能</strong>标注硬性技术要求</div>
      <div class="tip"><strong>加分项</strong>识别优先条件</div>
    </div>

    <div class="editor-wrap anim-fade-up anim-delay-2">
      <textarea v-model="jdText" placeholder="在此粘贴目标岗位的 JD 描述...&#10;&#10;例如：岗位职责、任职要求、薪资范围等"></textarea>
      <div class="editor-meta">
        <span>{{ jdText.length }} 字 · JD 过短可能影响解析质量</span>
        <button class="btn" :disabled="loading || !jdText.trim()" @click="handleParse">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'AI 解析中...' : '解析 JD' }}
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
</style>
