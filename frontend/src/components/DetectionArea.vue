<template>
  <div class="detection-area">
    <div class="detection-header">
      检测显示区域
    </div>

    <div class="detection-content">
      <template v-if="imgStore.transferredFileNames.length > 0">
        <!-- 使用 aspect-ratio 控制容器比例 -->
        <div class="image-wrapper">
          <img
            v-if="currentImageUrls"
            :src="currentImageUrls"
            alt="Selected PCB"
            class="responsive-image"
          />
        </div>
      </template>
      <template v-else>
        <div class="text-center">
          <div
            class="bg-gray-200 border-2 border-dashed border-gray-300 rounded-xl w-64 h-48 mx-auto"
          ></div>
          <p class="mt-6 text-gray-500">
            暂无内容
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>

import {useImageStore} from "../stores/manageImg.js";
import {computed} from "vue";

const imgStore = useImageStore()
const currentImageUrls = computed(() => {
  return imgStore.getMarkedImageUrlByIndex(imgStore.index)
})

</script>

<style scoped>
.detection-area {
  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  flex: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detection-header {
  background: linear-gradient(135deg, #4b5563, #1f2937);
  color: #e5e7eb;
  padding: 8px 16px;
  font-size: 0.9rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  flex-shrink: 0;
}

.detection-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f1f5f9;
  overflow: hidden;
}

/* ✅ 新增容器：固定宽度 + 等比缩放 */
.image-wrapper {
  width: 100%;
  max-width: 800px;
  aspect-ratio: 4 / 3;
  position: relative;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ✅ 图片本身等比缩放、居中显示 */
.responsive-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

/* 检测显示区域 - 关键修改 */
.detection-area {
  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  flex: 2;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许内容压缩 */
}

.detection-header {
  background: linear-gradient(135deg, #4b5563, #1f2937);
  color: #e5e7eb;
  padding: 8px 16px;
  font-size: 0.9rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  flex-shrink: 0;
}

/* 检测内容区域 - 关键修改 */
.detection-content {
  flex: 1;
  min-height: 0;
  position: relative;
  background-color: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 图片容器优化 */
.image-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  max-height: 100%;
}
</style>
