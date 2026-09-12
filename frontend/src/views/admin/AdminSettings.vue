<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getSystemInfo, listUsers, updateUserRole, type AdminUser, type SystemInfo } from '@/api/admin'

const settings = ref({
  database: {
    type: 'PostgreSQL',
    status: '连接正常',
    size: '128MB'
  },
  llm: {
    provider: 'DeepSeek',
    model: 'deepseek-chat',
    temperature: 0.3
  },
  rag: {
    chunkSize: 800,
    chunkOverlap: 80,
    topK: 5,
    similarityThreshold: 0.5
  }
})

const systemStats = ref<SystemInfo | null>(null)
const users = ref<AdminUser[]>([])
const loading = ref(true)
const error = ref('')

// 获取系统统计（真实数据）
const fetchSystemInfo = async () => {
  try {
    systemStats.value = await getSystemInfo()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取系统信息失败'
    console.error('获取系统信息失败:', err)
  }
}

// 获取用户列表（真实数据）
const fetchUsers = async () => {
  try {
    error.value = ''
    users.value = await listUsers()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取用户列表失败'
    console.error('获取用户列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 修改用户角色
const handleSetRole = async (user: AdminUser, role: 'user' | 'admin') => {
  if (user.role === role) return

  try {
    await updateUserRole(user.id, role)
    showAlert(`已将用户「${user.username}」的角色更新为 ${role === 'admin' ? '管理员' : '普通用户'}`)
    await fetchUsers()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '角色更新失败'
    console.error('角色更新失败:', err)
  }
}

// 显示提示（模板中无法直接访问 window.alert）
const showAlert = (message: string) => {
  alert(message)
}

onMounted(async () => {
  await Promise.all([fetchSystemInfo(), fetchUsers()])
})
</script>

<template>
  <div class="admin-settings-page">
    <main class="content">
      <h2 class="page-title anim-fade-up">系统设置</h2>
      <p class="page-sub anim-fade-up anim-delay-1">配置系统和管理用户</p>

      <!-- 系统信息（真实统计） -->
      <div class="settings-section anim-fade-up anim-delay-2">
        <h3>系统信息</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>用户数</label>
            <p>{{ systemStats?.user_count ?? '—' }}</p>
          </div>
          <div class="setting-item">
            <label>岗位分析数</label>
            <p>{{ systemStats?.job_count ?? '—' }}</p>
          </div>
          <div class="setting-item">
            <label>匹配报告数</label>
            <p>{{ systemStats?.match_report_count ?? '—' }}</p>
          </div>
          <div class="setting-item">
            <label>知识库文档数</label>
            <p>{{ systemStats?.knowledge_doc_count ?? '—' }}</p>
          </div>
        </div>
      </div>

      <!-- 数据库信息 -->
      <div class="settings-section anim-fade-up anim-delay-3">
        <h3>数据库</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>类型</label>
            <p>{{ settings.database.type }}</p>
          </div>
          <div class="setting-item">
            <label>状态</label>
            <span class="status-badge success">{{ settings.database.status }}</span>
          </div>
          <div class="setting-item">
            <label>存储大小</label>
            <p>{{ settings.database.size }}</p>
          </div>
        </div>
      </div>

      <!-- LLM配置 -->
      <div class="settings-section anim-fade-up anim-delay-4">
        <h3>大语言模型配置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>提供商</label>
            <p>{{ settings.llm.provider }}</p>
          </div>
          <div class="setting-item">
            <label>模型</label>
            <p>{{ settings.llm.model }}</p>
          </div>
          <div class="setting-item">
            <label>温度</label>
            <p>{{ settings.llm.temperature }}</p>
          </div>
        </div>
      </div>

      <!-- RAG配置 -->
      <div class="settings-section anim-fade-up anim-delay-5">
        <h3>RAG配置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>块大小</label>
            <p>{{ settings.rag.chunkSize }}</p>
          </div>
          <div class="setting-item">
            <label>块重叠</label>
            <p>{{ settings.rag.chunkOverlap }}</p>
          </div>
          <div class="setting-item">
            <label>Top-K</label>
            <p>{{ settings.rag.topK }}</p>
          </div>
          <div class="setting-item">
            <label>相似度阈值</label>
            <p>{{ settings.rag.similarityThreshold }}</p>
          </div>
        </div>
      </div>

      <!-- 用户管理（真实数据） -->
      <div class="settings-section anim-fade-up anim-delay-6">
        <div class="section-header">
          <h3>用户管理</h3>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>

        <div v-else class="users-table">
          <div v-if="users.length === 0" class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="8.5" cy="7" r="4"></circle>
              <line x1="20" y1="8" x2="20" y2="14"></line>
              <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
            <p>暂无用户</p>
            <p class="hint">添加第一个用户开始使用系统</p>
          </div>

          <table v-else class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.id }}</td>
                <td class="username">{{ user.username }}</td>
                <td>{{ user.email || '—' }}</td>
                <td>
                  <span class="role-badge" :class="user.role">
                    {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="user.role === 'user'"
                    class="role-btn promote"
                    @click="handleSetRole(user, 'admin')"
                  >
                    设为管理员
                  </button>
                  <button
                    v-else
                    class="role-btn demote"
                    @click="handleSetRole(user, 'user')"
                  >
                    设为普通用户
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-settings-page { position: relative; }

/* 主体 */
.content { padding: 0; max-width: 1100px; margin: 0 auto; }
.page-title { font-size: 1.5rem; color: #1a202c; }
.page-sub { color: #718096; margin: 0.3rem 0 1.8rem; }

/* 设置区域 */
.settings-section {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  margin-bottom: 1.5rem;
}
.settings-section h3 { font-size: 1.1rem; margin-bottom: 1rem; color: #2d3748; }
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.setting-item label {
  font-weight: 500;
  color: #4a5568;
  font-size: 0.85rem;
}
.setting-item p {
  font-weight: 600;
  color: #2d3748;
}
.status-badge {
  display: inline-block;
  padding: 0.2rem 0.8rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
}
.status-badge.success {
  background: rgba(72, 187, 120, 0.1);
  color: #48bb78;
}

/* 用户管理 */
.settings-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.add-user-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.add-user-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}
.users-table {
  overflow-x: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
}
.table th, .table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.table th {
  font-size: 0.85rem;
  color: #718096;
  font-weight: 600;
}
.table td { color: #4a5568; font-size: 0.92rem; }
.table .username { font-weight: 600; color: #2d3748; }
.role-badge {
  display: inline-block;
  padding: 0.15rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}
.role-badge.admin { background: rgba(102,126,234,0.12); color: #5a67d8; }
.role-badge.user { background: rgba(72,187,120,0.1); color: #38a169; }
.role-btn {
  padding: 0.35rem 0.8rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}
.role-btn.promote { color: #5a67d8; }
.role-btn.promote:hover { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff; border-color: transparent; }
.role-btn.demote { color: #e53e3e; border-color: #fc8181; }
.role-btn.demote:hover { background: #e53e3e; color: #fff; border-color: transparent; }
.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(102,126,234,0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}
.error p { color: #e53e3e; }
.empty-state svg { margin: 0 auto 1rem; opacity: 0.3; }
.empty-state p { color: #718096; margin-bottom: 0.5rem; }
.empty-state .hint { font-size: 0.9rem; color: #a0aec0; }

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>