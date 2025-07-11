// src/stores/imageStore.ts
import { defineStore } from 'pinia';
const RAW_ADDRESS = import.meta.env.VITE_RAW_ADDRESS
const MARKED_ADDRESS = import.meta.env.VITE_MARKED_ADDRESS
const SERVER_IP_DETECT = import.meta.env.VITE_SERVER_IP_DETECT;
const SERVER_PORT_DETECT = import.meta.env.VITE_SERVER_PORT_DETECT;
export const useImageStore = defineStore('imageStore', {
  state: () => ({
    transferredFileNames: [] as string[],
    timer: null as number | null,
    index: -1,
  }),

  getters: {
    getRawImageUrlByIndex: (state) => (index: number) => {
      // const SERVER_IP = import.meta.env.VITE_SERVER_IP;
      // const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;
      if (state.transferredFileNames.length === 0) return '';

      if (index < 0) index = state.transferredFileNames.length - 1;
      if (index >= state.transferredFileNames.length) index = 0;

      const fileName = state.transferredFileNames[index];
      return `http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}${RAW_ADDRESS}${fileName}`;
    },
    getMarkedImageUrlByIndex:(state) => (index: number) =>{
      // const SERVER_IP = import.meta.env.VITE_SERVER_IP;
      // const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;
      if (state.transferredFileNames.length === 0) return '';

      if (index < 0) index = state.transferredFileNames.length - 1;
      if (index >= state.transferredFileNames.length) index = 0;

      const fileName = state.transferredFileNames[index];
      const url = `http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}${MARKED_ADDRESS}${fileName}`;
      console.log("url:", url)
      return url;
    }
  },

  actions: {
    async callTransferApi() {
      // const SERVER_IP = import.meta.env.VITE_SERVER_IP;
      // const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;

      try {
        const response = await fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/transfer-images`, {
          method: 'GET'
        });
        const data = await response.json();
        if (data.status === 'ok') {
          this.transferredFileNames.push(...data.files);
          localStorage.setItem('transferredFileNames', JSON.stringify(data.files));
          console.log('✅ 已保存文件名列表:', data.files);
          if (this.index == -1){
            this.next_image()
            console.log("index:", this.index)
          }
        } else {
          console.warn('⚠️ 没有图片被转移');
        }
      } catch (err) {
        console.error('❌ 调用转移 API 失败:', err);
      }
    },

    startTimer() {
      if (this.timer) return;
      this.timer = window.setInterval(this.callTransferApi, 2000);
    },

    stopTimer() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    },

    next_image(){
      if (this.index >= this.transferredFileNames.length - 1) this.index = 0;
      else this.index++
    },

    pre_image(){
      if (this.index <= 0) this.index = this.transferredFileNames.length - 1;
      else this.index--
    }
  }
});
