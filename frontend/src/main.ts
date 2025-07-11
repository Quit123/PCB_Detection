import { createApp } from 'vue'
import { createPinia } from 'pinia'  // ✅ 引入 Pinia
import './style.css'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia) // ✅ 安装 Pinia 插件（必须）
app.mount('#app')
