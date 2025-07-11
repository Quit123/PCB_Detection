<template>
  <div class="control-panel">
    <h2>控制面板</h2>

    <!-- 模型选择 -->
    <section>
      <label>模型选择</label>
      <div class="button-group">
        <p class="current-model">当前模型：{{ mm.model }}</p>
        <button
          :class="['model-button', mm.model === 'custom' ? 'active' : '']"
          @click="handleModelButtonClick"
        >
          选择模型
        </button>
      </div>
      <!-- 模型列表显示 -->
      <div v-if="showModelOptions" class="model-select-wrapper">
        <label for="model-select">选择模型：</label>
        <select
          id="model-select"
          class="model-select"
          size="5"
          @change="onSelectChange"
          v-model="mm.model"
        >
          <!-- 模型列表 -->
          <option
            v-for="modelName in modelOptions"
            :key="modelName"
            :value="modelName"
          >
            {{ modelName }}
          </option>
        </select>
      </div>
    </section>

    <!-- 置信度设置 -->
    <section>
      <label>
        置信度阈值: <span class="conf-value">{{ mm.confidence.toFixed(2) }}</span>
      </label>
        <input
          type="range"
          min="0.01"
          max="0.99"
          step="0.01"
          :value="mm.confidence"
          @input="mm.confidence = parseFloat(($event.target as HTMLInputElement).value)"
        >
    </section>

    <!-- 操作按钮 -->
    <section class="button-group-vertical">
      <button
        :disabled="isProcessing || !canStart"
        @click="$emit('start-detect')"
        :class="['action-button primary', (isProcessing || !canStart) ? 'disabled' : '']"
      >
        ▶️ 开始检测
      </button>

      <button
        :disabled="!isProcessing"
        @click="$emit('stop-detect')"
        :class="['action-button danger', !isProcessing ? 'disabled' : '']"
      >
        ⏹ 停止检测
      </button>

      <button
        :disabled="!hasDetection"
        :class="['action-button secondary', !hasDetection ? 'disabled' : '']"
      >
        💾 保存结果
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import {computed} from "vue";
import { ref } from 'vue';
import { useManageModel } from '../stores/manageModel.ts'

const SERVER_IP_DETECT = import.meta.env.VITE_SERVER_IP_DETECT;
const SERVER_PORT_DETECT = import.meta.env.VITE_SERVER_PORT_DETECT;
// const RAW_ADDRESS = import.meta.env.RAW_ADDRESS;
const mm = useManageModel()

// 父传子，子按训练，父开始训练反传isProcessing，子按停止，检查isProcessing
defineProps<{
  mediaType: string
  isProcessing: boolean
  hasDetection: boolean
}>()

const emit = defineEmits<{
  (e: 'select-image'): void
  (e: 'select-folder'): void
  (e: 'start-detect'): void
  (e: 'stop-detect'): void
}>()

const canStart = computed(() => {
  return true // 父组件可根据选中图片动态传递
})

const handleModelButtonClick = () => {
  loadModelList();  // 异步加载模型列表
};

// 读取列表
const modelOptions = ref<string[]>([]);
const showModelOptions = ref(false);
const onSelectChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const selectedModel = target.value;
  mm.model = selectedModel;  // ✅ 使用 Pinia 存储模型名称
  showModelOptions.value = false;  // ✅ 可选：收起选择框
  console.log("✅ 选择了模型:", selectedModel);
};

const loadModelList = async () => {
  try {
    const response = await fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/return_model`);
    const data = await response.json();

    if (data.status === 'success') {
      modelOptions.value = data.model_dirs;
      showModelOptions.value = true;
      console.log("modelOptions.value:\n", modelOptions.value)
    } else {
      console.warn('⚠️ 获取模型列表失败:', data.message);
    }
  } catch (err) {
    console.error('❌ 请求模型列表失败:', err);
  }
};

</script>


<style scoped>

.model-select-wrapper {
  margin-top: 10px;
  width: 200px;
}

.model-select {
  width: 100%;
  height: auto;
  padding: 5px;
  font-size: 14px;
  overflow-y: auto;
}

.control-panel {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

h2 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #333;
}

section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 600;
  color: #555;
  margin-bottom: 4px;
}

.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.button-group-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-button {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ccc;
  background: #f9f9f9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.model-button:hover {
  background: #eee;
}

.model-button.active {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.action-button {
  padding: 10px;
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s ease;
}

.action-button.primary {
  background: #3b82f6;
}

.action-button.primary:hover {
  background: #2563eb;
}

.action-button.danger {
  background: #ef4444;
}

.action-button.danger:hover {
  background: #dc2626;
}

.action-button.secondary {
  background: #6b7280;
}

.action-button.secondary:hover {
  background: #4b5563;
}

.action-button.disabled,
.action-button:disabled {
  background: #cbd5e1 !important;
  cursor: not-allowed;
}

.confidence-slider {
  width: 100%;
}

.conf-value {
  color: #3b82f6;
  font-family: monospace;
}
</style>