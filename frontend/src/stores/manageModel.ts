// src/stores/manageModel.ts
import {defineStore} from 'pinia';

// const SERVER_IP = import.meta.env.VITE_SERVER_IP;
// const SERVER_PORT = import.meta.env.VITE_SERVER_PORT;
const SERVER_IP_DETECT = import.meta.env.VITE_SERVER_IP_DETECT
const SERVER_PORT_DETECT = import.meta.env.VITE_SERVER_PORT_DETECT

export const useManageModel = defineStore('detection', {
    state: () => ({
        model: '暂无',
        terminate_model: '暂无',
        confidence: 0.25,
        mediaType: 'image' as 'image' | 'folder',
        isProcessing: false,
        hasDetection: false,
        selectedImage: null as File | null,
        modelTraining: false,
    }),

    getters: {
        // 可按需添加 getter，例如状态描述
        statusText(state) {
            return state.isProcessing
                ? '检测中...'
                : state.hasDetection
                    ? '检测完成'
                    : '等待检测';
        },
    },

    actions: {
        startDetect() {
            if (!this.selectedImage) return;
            this.isProcessing = true;

            setTimeout(() => {
                this.hasDetection = true;
                this.isProcessing = false;
            }, 2000);
        },

        stopDetect() {
            this.isProcessing = false;
            this.hasDetection = false;
        },

        startTraining() {
            this.modelTraining = true;
        },

        stopTraining() {
            this.modelTraining = false;
        },

        async startDetection() {
            // model.value = mm.model
            console.log("startDetection model:", this.model)
            console.log("置信度设置：", this.confidence)

            this.isProcessing = true
            // ✅ 发请求给后端，打开active_learning
            try {
                const response = await fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/start-detecting`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        model_name: this.model
                    })
                })

                const data = await response.json()
                if (data.status === 'started') {
                    console.log('✅ 后端模型启动成功，PID:', data.pid)
                } else {
                    console.warn('⚠️ 后端启动失败:', data.message)
                }
            } catch (err) {
                console.error('❌ 请求出错:', err)
            }
        },

        async stopDetection() {
            // detectionResults.value = []
            try {
                const response = await fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/stop-detecting`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        model_name: this.terminate_model
                    })
                });
                const data = await response.json();

                if (data.status === 'stopped' || data.status === 'killed') {
                    console.log(`✅ 后端进程已终止: ${data.status}, PID: ${data.pid}`);
                } else {
                    console.warn('⚠️ 后端没有正在运行的进程:', data.status);
                }
            } catch (err) {
                console.error('❌ 停止检测请求失败:', err);
            }
            this.isProcessing = false;
        }
    },
});
