<template>
  <div class="training-container">

    <div class="control-section">
      <div v-if="!trainingId">
        <button
          @click="startTraining"
          :disabled="isProcessing"
          class="start-button"
        >
          <span v-if="isProcessing">
            <i class="spinner"></i> 启动中...
          </span>
          <span v-else>开始训练</span>
        </button>
      </div>

      <div v-else class="training-info">
        <div class="status-line">
          <label>训练ID:</label>
          <span class="id-text">{{ trainingId }}</span>
        </div>

        <div class="status-line">
          <label>状态:</label>
          <span :class="statusClass">{{ statusText }}</span>
        </div>

        <button
          @click="stopTraining"
          class="stop-button"
          :disabled="trainingStatus !== 'running'"
        >
          停止训练
        </button>
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>

    <!-- 训练完成弹窗 -->
    <div v-if="showCompletionModal" class="completion-modal">
      <div class="modal-content">
        <div class="checkmark">✓</div>
        <h3>训练完成！</h3>

        <!-- 添加训练名称显示 -->
        <p class="training-name">{{ trainingName }} - 训练完成</p>

        <div class="model-path">
          <label>模型保存位置:</label>
          <!-- 显示完整路径，并添加可点击图标 -->
          <div class="path-container">
            <div class="path">{{ actualModelPath }}</div>
            <button @click="copyActualModelPath" class="copy-icon" title="复制路径">
              📋
            </button>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="copyActualModelPath" class="copy-button">复制路径</button>
          <button @click="closeCompletionModal" class="close-button">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import {useManageModel} from "../stores/manageModel.js"

const trainingId = ref('')
const trainingStatus = ref('') // pending, running, completed, failed
const isProcessing = ref(false)
const errorMessage = ref('')
const showCompletionModal = ref(false)
// const modelPath = ref('')
const actualModelPath = ref('实际保存路径将在此显示') // 修改为直接存储实际路径
// const socket = ref(null)
const trainingName = ref('YOLOv11 PCB检测') // 训练名称
const manageModel = useManageModel()
const modelOptions = ref<string[]>([]);

const SERVER_IP = import.meta.env.VITE_SERVER_IP;
const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;
const SERVER_IP_DETECT = import.meta.env.VITE_SERVER_IP_DETECT;
const SERVER_PORT_DETECT = import.meta.env.VITE_SERVER_PORT_DETECT;

// 状态文本
const statusText = computed(() => {
  switch (trainingStatus.value) {
    case 'pending': return '等待开始'
    case 'running': return '训练中...'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'stopped': return '已停止'
    default: return trainingStatus.value
  }
})

// 状态样式
const statusClass = computed(() => {
  return {
    'status-text': true,
    'status-pending': trainingStatus.value === 'pending',
    'status-running': trainingStatus.value === 'running',
    'status-completed': trainingStatus.value === 'completed',
    'status-failed': trainingStatus.value === 'failed',
    'status-stopped': trainingStatus.value === 'stopped'
  }
})

const startTraining = async () => {
  try {
    isProcessing.value = true
    errorMessage.value = ''
    trainingStatus.value = 'pending'

    // 调用后端API启动训练
    const response = await axios.post(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/managing-data`)

    if (response.data.pid) {

      trainingId.value = response.data.training_id
      trainingStatus.value = 'running'
      // 连接WebSocket获取状态更新
      manageModel.startTraining()
      connectSocket()
    }
  } catch (error) {
    handleError(error)
  } finally {
    isProcessing.value = false
  }
}

const connectSocket = async () => {
  try {
    console.log("into connectSocket...")
    await waitUntilUploadComplete() // 等待解压完成
    console.log("backend_model finish")

    const response = await fetch(`http://${SERVER_IP}:${SERVER_PORT}/api/managing-training`, {
      method: 'POST'
    });
    const data = await response.json();
    if(data.status)console.log("start training...")

    // ✅ 上传 + 解压完成，继续建立 WebSocket 并监听训练完成
    const socket = new WebSocket(`ws://${SERVER_IP}:${SERVER_PORT}/ws/training-status`)
    socket.onmessage = (event) => {
      const message = event.data
      if (message === "training_complete") {
        manageModel.stopTraining()
        alert("训练完成！")
        console.log("训练完成！")
        autoChangeModel()
      }
    }

    // 👉 你也可以在这里开始调用训练接口，例如：
    // await fetch(`http://${SERVER_IP}:${SERVER_PORT}/api/managing-training`, { method: 'POST' })

  } catch (err) {
    alert("❌ 解压失败或超时：" + err)
  }
}

const waitUntilUploadComplete = async (maxTries = 30, interval = 2000): Promise<void> => {
  let tries = 0

  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      tries++
      if (tries > maxTries) {
        clearInterval(timer)
        reject("⏹️ 超过最大轮询次数，上传未完成")
        return
      }

      try {
        const response = await fetch(`http://${SERVER_IP}:${SERVER_PORT}/upload-status/`)
        const data = await response.json()
        if (data.done === true) {
          clearInterval(timer)
          console.log("✅ 解压已完成")
          resolve()
        } else {
          console.log("⌛ 解压未完成，继续轮询")
        }
      } catch (err) {
        console.error("❌ 检查上传状态失败：", err)
      }
    }, interval)
  })
}



const stopTraining = async () => {
  if (!trainingId.value) return
  try {
    trainingStatus.value = 'stopping'
    await axios.post(`http://${SERVER_IP}:${SERVER_PORT}/api/stop-training/${trainingId.value}`)
    trainingStatus.value = 'stopped'
  } catch (error) {
    handleError(error)
  }
}


const autoChangeModel = async () => {
  try {
    console.log("🧪 SERVER_IP_DETECT:", SERVER_IP_DETECT);
    console.log("🧪 SERVER_PORT_DETECT:", SERVER_PORT_DETECT);
    console.log(`🧪 拼接地址: http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/return_model`);
    const response = await fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/return_model`);
    const data = await response.json();
    if (data.status === 'success') {
      modelOptions.value = data.model_dirs;
      if (modelOptions.value.length > 0) {
        // 自动选中最新的模型
        manageModel.terminate_model = manageModel.model
        manageModel.model = modelOptions.value[0]
        console.log("✅ 最新模型已自动选中:", manageModel.model)
        await manageModel.stopDetection()
        await manageModel.startDetection()
      }
      console.log("modelOptions.value:\n", modelOptions.value)
    } else {
      console.warn('⚠️ 获取模型列表失败:', data.message);
    }
  } catch (err) {
    console.error('❌ 请求模型列表失败:', err);
  }
};

// 复制实际模型路径
const copyActualModelPath = () => {
  if (actualModelPath.value) {
    navigator.clipboard.writeText(actualModelPath.value)
    alert('模型路径已复制到剪贴板')
  }
}

const closeCompletionModal = () => {
  showCompletionModal.value = false
}

const handleError = (error: any) => {
  if (error.response) {
    errorMessage.value = `服务器错误: ${error.response.status} - ${error.response.data.error || '未知错误'}`
  } else if (error.request) {
    errorMessage.value = '服务器未响应，请检查后端是否运行'
  } else {
    errorMessage.value = `请求错误: ${error.message}`
  }
  // 发生错误时重置状态
  trainingStatus.value = 'failed'
}

// onBeforeUnmount(() => {
//   // 使用重置函数替代原有代码
//   resetTrainingState()
// })
</script>

<style scoped>
/* 添加返回按钮样式 */
.training-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  background-color:rgb(249, 249, 252);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #e0e0ff;
}
/* 调整容器位置，为返回按钮留出空间 */
.training-container {
  position: relative;
  max-width: 600px;
  margin: 40px auto;
  padding: 60px 20px 20px; /* 顶部内边距增加到60px */
  background-color:rgb(249, 249, 252);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #e0e0ff;
}

.control-section {
  padding: 20px;
  text-align: center;
}

h2 {
  font-size: 24px;
  margin-bottom: 24px;
  color: #b4b4ff;
}

button {
  cursor: pointer;
  border: none;
  border-radius: 6px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s;
}

.start-button {
  background: linear-gradient(135deg,rgb(17, 203, 116) 0%,rgb(37, 252, 227) 100%);
  color: white;
  box-shadow: 0 4px 8px rgba(250, 252, 254, 0.3);
}

.start-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(37, 117, 252, 0.4);
}

.start-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.training-info {
  text-align: left;
  background-color:rgb(244, 245, 249);
  border-radius: 8px;
  padding: 20px;
  margin: 24px 0;
}

.status-line {
  display: flex;
  margin-bottom: 14px;
}

label {
  font-weight: 600;
  color: #8a9cb0;
  min-width: 80px;
}

.id-text {
  font-family: monospace;
  background-color:rgb(62, 121, 241);
  padding: 4px 10px;
  border-radius: 4px;
}

.stop-button {
  display: block;
  width: 100%;
  margin-top: 20px;
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  color: white;
}

.stop-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(255, 75, 43, 0.4);
}

.stop-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  margin-top: 20px;
  padding: 12px;
  border-radius: 6px;
  background-color: #ff4d4f29;
  color: #ff4d4f;
  border: 1px solid #ff4d4f50;
  text-align: center;
}

.completion-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: #2d3748;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 30px;
  text-align: center;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
}

.checkmark {
  font-size: 60px;
  color: #10b981;
  margin-bottom: 20px;
}

h3 {
  color: white;
  font-size: 26px;
  margin-bottom: 10px;
}

p {
  color: #cbd5e1;
  margin-bottom: 20px;
}

.model-path {
  text-align: left;
  margin: 25px 0;
}

.model-path label {
  display: block;
  color: #93c5fd;
  margin-bottom: 6px;
}

.path {
  background-color: #1e293b;
  border-radius: 6px;
  padding: 12px;
  font-family: monospace;
  word-break: break-all;
  color: #e2e8f0;
  white-space: pre-wrap; /* 保留空白符 */
}

.path-container {
  display: flex;
  align-items: center;
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.modal-actions button {
  flex: 1;
  padding: 12px;
}

.copy-button {
  background: #6366f1;
  color: white;
}

.copy-button:hover {
  background: #4f46e5;
}

.close-button {
  background: #4b5563;
  color: #e5e7eb;
}

.close-button:hover {
  background: #374151;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 训练名称样式 */
.training-name {
  font-size: 16px;
  color: #a0aec0;
  margin-bottom: 20px;
  font-weight: 600;
}

/* 复制图标样式 */
.copy-icon {
  background: none;
  border: none;
  color: #93c5fd;
  cursor: pointer;
  font-size: 18px;
  margin-left: 10px;
  transition: transform 0.2s;
}

.copy-icon:hover {
  transform: scale(1.2);
  color: #63b3ed;
}
</style>