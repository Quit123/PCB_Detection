<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue';
const SERVER_IP = import.meta.env.VITE_SERVER_IP;
const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;
// const RAW_ADDRESS = import.meta.env.RAW_ADDRESS;

let timer: number | undefined;
// const url = `http://${server_ip}:${port}${fileUrl}`
let transferredFileNames: string[] = [];

// 调用 API，获取文件名列表：这里的localStorage还没有做下载
const callTransferApi = async () => {
  try {
    const response = await fetch(`https://${SERVER_IP}:${SERVER_PORT}/api/transfer-images`, {
      method: 'POST'
    });
    const data = await response.json();
    if (data.status === 'ok') {
      transferredFileNames = data.files;  // 存在内存中
      console.log('✅ 已保存文件名列表:', transferredFileNames);
      // 你也可以持久化，比如：
      localStorage.setItem('transferredFileNames', JSON.stringify(transferredFileNames));
    } else {
      console.warn('⚠️ 没有图片被转移');
    }
  } catch (err) {
    console.error('❌ 调用转移 API 失败:', err);
  }
};

onMounted(() => {
  timer = window.setInterval(callTransferApi, 2000);
});

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer);
  }
});

// 根据 index 获取图片 URL
// const getImageUrlByIndex = (index:number) => {
//   if (index < 0){
//     index = transferredFileNames.length - 1;
//   }
//   if (index >= transferredFileNames.length){
//     index = 0
//   }
//   const fileName = transferredFileNames[index];
//   return `http://${SERVER_IP}:${SERVER_PORT}${RAW_ADDRESS}${fileName}`;
// };

</script>

<template>
  <!-- 没有展示，仅定时调用 -->
</template>

<style scoped>
</style>
