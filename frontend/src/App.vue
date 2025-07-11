<template>
  <div class="app-container">
    <header class="header-gradient">
      <div class="flex items-center">
        <div class="bg-white rounded-full p-2 mr-3">
          <div class="bg-gray-200 border-2 border-dashed rounded-xl w-10 h-10"></div>
        </div>
        <h1 class="text-2xl font-bold">基于YOLOv8的PCB缺陷检测系统</h1>
      </div>
    </header>

    <main class="main-layout">
      <div class="left-panel control-panel">
        <ControlPanel
          :mediaType="mediaType"
          :isProcessing="mm.isProcessing"
          :hasDetection="detectionResults.length > 0"
          @select-image="triggerImageSelect"
          @select-folder="triggerFolderSelect"
          @start-detect="beginDetection"
          @stop-detect="endDetection"/>
        <div>
          <h1>训练页面</h1>
          <TrainState />  <!-- 这里渲染按钮组件 -->
        </div>
      </div>

      <div class="middle-area">
        <DetectionArea
          :image="selectedImage"
          :results="detectionResults"
          :mediaType="mediaType"
          :folderImages="folderImages"
          :currentIndex="currentImageIndex"
          :isPlaying="isPlaying"
          :isProcessing="mm.isProcessing"
        />
        <ResultTable :results="detectionResults" />
      </div>

      <div class="right-area">
        <LabelArea />
      </div>
    </main>

    <!-- 文件选择 input -->
    <input
      type="file"
      ref="fileInput"
      style="display: none"
      accept="image/*"
      @change="handleFileChange"
    />
    <input
      type="file"
      ref="folderInput"
      style="display: none"
      multiple
      @change="handleFolderChange"
    />
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import DetectionArea from './components/DetectionArea.vue'
import ResultTable from './components/ResultTable.vue'
import TrainState from './components/TrainState.vue'
import LabelArea from "./components/LabelArea.vue";
import {useManageModel} from "./stores/manageModel.js";
import {useImageStore} from "./stores/manageImg.js";

const model = ref('未选择')
const confidence = ref(0.25)
const mediaType = ref('image')
const detectionResults = ref([])
// const isProcessing = ref(false)
const selectedImage = ref(null)
const folderImages = ref([])
const currentImageIndex = ref(0)
const isPlaying = ref(false)

const fileInput = ref(null)
const folderInput = ref(null)

const mm = useManageModel()
const is = useImageStore()

let interval = null

function triggerImageSelect() {
  mediaType.value = 'image'
  fileInput.value.click()
}

function triggerFolderSelect() {
  mediaType.value = 'folder'
  folderInput.value.click()
}

function handleFileChange(event) {
  const file = event.target.files[0]
  if (file) {
    folderImages.value = []
    isPlaying.value = false
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

function handleFolderChange(event) {
  const files = Array.from(event.target.files)
  const imageFiles = files.filter(f =>
    f.type.startsWith('image/') && /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(f.name)
  )
  if (imageFiles.length === 0) {
    alert('选择的文件夹中没有图片文件')
    return
  }

  folderImages.value = imageFiles.map(f => ({
    name: f.name,
    url: URL.createObjectURL(f),
    file: f
  }))
  selectedImage.value = folderImages.value[0].url
  currentImageIndex.value = 0
  mediaType.value = 'folder'
  isPlaying.value = true
  detectionResults.value = []
}

function nextImage() {
  currentImageIndex.value = (currentImageIndex.value + 1) % folderImages.value.length
}

function prevImage() {
  currentImageIndex.value = currentImageIndex.value === 0
    ? folderImages.value.length - 1
    : currentImageIndex.value - 1
}

function beginDetection(){
  mm.startDetection()
  is.startTimer()
}

function endDetection(){
  mm.terminate_model = mm.model
  mm.stopDetection()
  is.stopTimer()
}

watch([isPlaying, folderImages], () => {
  clearInterval(interval)
  if (isPlaying.value && folderImages.value.length > 1) {
    interval = setInterval(() => {
      nextImage()
    }, 3000)
  }
})

watch(currentImageIndex, () => {
  if (folderImages.value.length > 0) {
    selectedImage.value = folderImages.value[currentImageIndex.value].url
  }
})

onUnmounted(() => {
  folderImages.value.forEach(img => URL.revokeObjectURL(img.url))
  clearInterval(interval)
})
</script>


<style scoped>

.app-container {
  display: flex;
  flex-direction: column;
  height: 98vh;
  width: 100%;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;  /* 禁止 app-container 滚动 */
}

/* 顶部标题栏 */
.header-gradient {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 12px 20px;
  flex-shrink: 0;
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  width: 100%;
}

/* 主内容区域 - 关键修改 */
.main-layout {
  display: flex;
  flex: 1;
  min-height: 0; /* 允许内容压缩 */
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.left-panel {
  width: 20%;
  min-width: 280px;
  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* 右侧区域 - 关键修改 */
.middle-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  height: 100%;
}

.right-area {
  flex: 1;                 /* 占据等比例空间 */
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  height: 100%;
}


.image-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

</style>