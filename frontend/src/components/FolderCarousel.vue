<template>
  <div class="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-lg">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      文件夹控制
    </label>

    <div class="mb-2 text-sm">
      已加载 {{ folderImages.length }} 张图片
    </div>

    <div class="grid grid-cols-3 gap-2">
      <button
        @click="$emit('prev')"
        class="action-button secondary-button"
      >
        上一张
      </button>

      <button
        @click="$emit('next')"
        class="action-button secondary-button"
      >
        下一张
      </button>
    </div>

    <div class="mt-3 text-xs flex justify-between">
      <span>当前: {{ currentIndex + 1 }} / {{ folderImages.length }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  folderImages: Array,
  currentIndex: Number,
})

defineEmits(['prev', 'next', 'toggle'])
</script>

<style scoped>
/* 你可以引入原样式或在这里定义必要样式 */
</style>
