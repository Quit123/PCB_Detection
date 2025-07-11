<template>
  <div class="result-area">
    <div class="result-header">
      检测结果
    </div>
    <div class="overflow-auto max-h-60 p-4">
      <table class="result-table w-full text-sm">
        <thead>
          <tr>
            <th>序号</th>
            <th>类别</th>
            <th>置信度</th>
            <th>位置(x,y,w,h)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="results.length === 0">
            <td colspan="4" class="text-center py-8 text-gray-500">
              暂无检测结果，请开始检测
            </td>
          </tr>
          <tr v-for="(result, index) in results" :key="result.id">
            <td>{{ index + 1 }}</td>
            <td>
              <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                {{ result.class }}
              </span>
            </td>
            <td>
              <div class="flex items-center">
                <div class="w-24 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    class="h-2 rounded-full"
                    :class="{
                      'bg-green-500': result.confidence > 0.8,
                      'bg-yellow-500': result.confidence > 0.6 && result.confidence <= 0.8,
                      'bg-red-500': result.confidence <= 0.6
                    }"
                    :style="{ width: (result.confidence * 100) + '%' }"
                  ></div>
                </div>
                <span class="text-xs text-gray-600">
                  {{ (result.confidence * 100).toFixed(1) }}%
                </span>
              </div>
            </td>
            <td>
              ({{ result.position.x }}, {{ result.position.y }},
              {{ result.position.w }}, {{ result.position.h }})
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  results: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>


/* 结果区域 - 关键修改 */
.result-area {
  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.result-header {
  background: linear-gradient(135deg, #4b5563, #1f2937);
  color: #e5e7eb;
  padding: 8px 16px;
  font-size: 0.9rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  flex-shrink: 0;
}


</style>
