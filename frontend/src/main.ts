import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { initializeAuth } from './router/guards'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 初始化时检查用户状态
initializeAuth()

app.mount('#app')
