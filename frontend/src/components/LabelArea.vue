<script setup lang="ts">
import {ref, reactive, onMounted, computed, watch} from 'vue'
const SERVER_IP_DETECT = import.meta.env.VITE_SERVER_IP_DETECT;
const SERVER_PORT_DETECT = import.meta.env.VITE_SERVER_PORT_DETECT;

import {useImageStore} from "../stores/manageImg.js";


interface Box {
  class_id: number
  xmin: number
  ymin: number
  xmax: number
  ymax: number
}

// 图片和标注数据
const boxes = reactive<Record<number, Box[]>>({}) // key: image index
const annotationList = ref<Box[]>([])

const canvasRef = ref<HTMLCanvasElement | null>(null)
const imgStore = useImageStore()
const currentImageUrl = computed(() => {
  return imgStore.getRawImageUrlByIndex(imgStore.index)
})

let startX = 0
let startY = 0
let drawing = false
let cachedImg: HTMLImageElement | null = null
let ctx: CanvasRenderingContext2D | null = null
let scale = 1
let offsetX = 0
let offsetY = 0

onMounted(() => {
  const canvas = canvasRef.value!
  const container = canvas.parentElement!
  canvas.width = container.clientWidth
  canvas.height = canvas.width * 0.75  // 保持 4:3
  ctx = canvas.getContext("2d")
  drawImageOnCanvas()
})

watch(currentImageUrl, () => {
  if (currentImageUrl.value) drawImageOnCanvas()
})

watch(() => imgStore.index, () => {
  annotationList.value = [...(boxes[imgStore.index] || [])]
})

const drawImageOnCanvas = () => {
  if (canvasRef.value === null) {
    console.log("drawImageOnCanvas: canvasRef.value === null")
    return;
  }
  const canvas = canvasRef.value
  if (canvas === null) {
    console.log("drawImageOnCanvas: canvas === null")
    return;
  }
  const ctx = canvasRef.value!.getContext('2d')
  if (ctx ===null) {
    console.log("drawImageOnCanvas: ctx === null")
    return;
  }
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    cachedImg = img
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    scale = Math.min(canvas.width / img.width, canvas.height / img.height)
    offsetX = (canvas.width - img.width * scale) / 2
    offsetY = (canvas.height - img.height * scale) / 2

    ctx.drawImage(img, 0, 0, img.width, img.height,
                  offsetX, offsetY, img.width * scale, img.height * scale)

    // 画框逻辑也要加 offset 和 scale
    for (const box of boxes[imgStore.index] || []) {
      ctx.strokeStyle = '#c586c0'
      ctx.lineWidth = 2
      ctx.strokeRect(
        box.xmin * scale + offsetX,
        box.ymin * scale + offsetY,
        (box.xmax - box.xmin) * scale,
        (box.ymax - box.ymin) * scale
      )
      ctx.fillStyle = '#c586c0'
      ctx.font = '12px Consolas'
      ctx.fillText(box.class_id.toString(),
                   box.xmin * scale + offsetX + 5,
                   box.ymax * scale + offsetY - 5)
    }
  }
  img.onerror = () => {
    console.warn("⚠️ 无法加载图片：", currentImageUrl.value)
  }
  if (!boxes[imgStore.index]) {
    boxes[imgStore.index] = []
  }
  img.src = currentImageUrl.value
}


// 导出标注
function exportLabels() {
  const promises = imgStore.transferredFileNames.map((fileName, idx) => {
    return new Promise<{ filename: string; labels: string[] }>((resolve) => {
      const img = new Image()
      img.crossOrigin = 'anonymous'

      img.onload = () => {
        const imgWidth = img.width
        const imgHeight = img.height

        const boxList = boxes[idx] || []
        const labelData = boxList.map(box => {
          const xCenter = ((box.xmin + box.xmax) / 2) / imgWidth
          const yCenter = ((box.ymin + box.ymax) / 2) / imgHeight
          const boxWidth = (box.xmax - box.xmin) / imgWidth
          const boxHeight = (box.ymax - box.ymin) / imgHeight

          return `${box.class_id} ${xCenter.toFixed(6)} ${yCenter.toFixed(6)} ${boxWidth.toFixed(6)} ${boxHeight.toFixed(6)}`
        })

        resolve({
          filename: fileName.replace(/\.\w+$/, ''), // 去扩展名
          labels: labelData
        })
      }

      img.onerror = () => {
        console.warn(`⚠️ 不能加载图片 ${fileName}`)
        resolve({
          filename: fileName.replace(/\.\w+$/, ''),
          labels: []
        })
      }

      img.src = imgStore.getMarkedImageUrlByIndex(idx)
    })
  })

  Promise.all(promises).then(results => {
    fetch(`http://${SERVER_IP_DETECT}:${SERVER_PORT_DETECT}/api/export_data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(results)
    }).then(res => {
      if (res.ok) {
        alert('✅ 标注已保存到服务器')
      } else {
        alert('❌ 导出失败')
      }
    })
  })
}



// 画框逻辑
function onMouseDown(e: MouseEvent) {
  if (!ctx) return
  drawing = true
  const rect = canvasRef.value!.getBoundingClientRect()
  const scaleX = canvasRef.value!.width / rect.width
  const scaleY = canvasRef.value!.height / rect.height
  startX = (e.clientX - rect.left) * scaleX
  startY = (e.clientY - rect.top) * scaleY
}

// 鼠标移动中直接画图，不重新 load 图片
function onMouseMove(e: MouseEvent) {
  if (!ctx || !drawing || !cachedImg) return
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const curX = (e.clientX - rect.left) * scaleX
  const curY = (e.clientY - rect.top) * scaleY

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(cachedImg, 0, 0, cachedImg.width, cachedImg.height,
                offsetX, offsetY, cachedImg.width * scale, cachedImg.height * scale)

  ctx.strokeStyle = '#c586c0'
  ctx.lineWidth = 2
  ctx.strokeRect(startX, startY, curX - startX, curY - startY)

  for (const box of boxes[imgStore.index] || []) {
    ctx.strokeRect(
      box.xmin * scale + offsetX,
      box.ymin * scale + offsetY,
      (box.xmax - box.xmin) * scale,
      (box.ymax - box.ymin) * scale
    )
    ctx.fillText(box.class_id.toString(),
                 box.xmin * scale + offsetX + 5,
                 box.ymax * scale + offsetY - 5)
  }
}

function onMouseUp(e: MouseEvent) {
  if (!ctx || !drawing) return
  drawing = false
  const rect = canvasRef.value!.getBoundingClientRect()
  const scaleX = canvasRef.value!.width / rect.width
  const scaleY = canvasRef.value!.height / rect.height
  const endX = (e.clientX - rect.left) * scaleX
  const endY = (e.clientY - rect.top) * scaleY

  const realStartX = (startX - offsetX) / scale
  const realStartY = (startY - offsetY) / scale
  const realEndX = (endX - offsetX) / scale
  const realEndY = (endY - offsetY) / scale

  const xmin = Math.min(realStartX, realEndX)
  const xmax = Math.max(realStartX, realEndX)
  const ymin = Math.min(realStartY, realEndY)
  const ymax = Math.max(realStartY, realEndY)

  const classInput = prompt('请输入 class_id:')
  if (classInput === null) {
    redraw()
    return
  }
  const class_id = Number(classInput)
  if (!isNaN(class_id)) {
    const box = { class_id, xmin, ymin, xmax, ymax }
    boxes[imgStore.index].push(box)
    annotationList.value = [...boxes[imgStore.index]]
  }
  redraw()
}


function redraw() {
  if (!ctx) return

  const canvas = canvasRef.value!
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.src = currentImageUrl.value

  img.onload = () => {
    ctx!.clearRect(0, 0, canvas.width, canvas.height)

    // ✅ 重新计算比例和偏移
    scale = Math.min(canvas.width / img.width, canvas.height / img.height)
    offsetX = (canvas.width - img.width * scale) / 2
    offsetY = (canvas.height - img.height * scale) / 2

    // ✅ 等比例绘制图像
    ctx!.drawImage(img, 0, 0, img.width, img.height,
                   offsetX, offsetY, img.width * scale, img.height * scale)

    // ✅ 绘制所有标注框（缩放 + 平移）
    for (const box of boxes[imgStore.index] || []) {
      ctx!.strokeStyle = '#c586c0'
      ctx!.lineWidth = 2
      ctx!.strokeRect(
        box.xmin * scale + offsetX,
        box.ymin * scale + offsetY,
        (box.xmax - box.xmin) * scale,
        (box.ymax - box.ymin) * scale
      )
      ctx!.fillStyle = '#c586c0'
      ctx!.font = '12px Consolas'
      ctx!.fillText(
        box.class_id.toString(),
        box.xmin * scale + offsetX + 5,
        box.ymax * scale + offsetY - 5
      )
    }
  }

  img.onerror = () => {
    console.warn("⚠️ redraw 无法加载图像：", currentImageUrl.value)
  }
}


const prevImage = () => {
  imgStore.pre_image()
}
const nextImage = () => {
  imgStore.next_image()
}

</script>

<template>
<div class="container">
  <div class="label-area">
      <div class="mark-header">
         图片标注区域
      </div>
    <div class="button-container">
      <button class="Prev-btn" @click="prevImage">上一个</button>
      <button class="Next-btn" @click="nextImage">下一个</button>
      <button class="Export-btn" @click="exportLabels">保存</button>
    </div>
    <canvas ref="canvasRef" width="800" height="600"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"></canvas>
  </div>
  <div class="annotation-list">
  <div class="result-header">
  标注信息 (图片 {{ imgStore.index + 1 }}/{{ imgStore.transferredFileNames.length }})
  </div>
  <ul>
    <li v-for="(box, idx) in annotationList" :key="idx">
      Class: {{ box.class_id }}
      [{{ box.xmin.toFixed(1) }}, {{ box.ymin.toFixed(1) }}] -
      [{{ box.xmax.toFixed(1) }}, {{ box.ymax.toFixed(1) }}]
    </li>
  </ul>
</div>
</div>
</template>

<style scoped>
.container {
  overflow-y: auto; /* 允许垂直滚动 */


}
.mark-header{
  background: linear-gradient(135deg, #4b5563, #1f2937);
  color: #e5e7eb;
  padding: 8px 16px;
  font-size: 0.9rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  flex-shrink: 0;

}
.label-area {

  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  flex: 2;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许内容压缩 */
}

.button-container {
  display: flex;          /* 启用 Flexbox */
  justify-content: center; /* 按钮在容器内水平居中 (可选，根据你的布局需求) */
  gap: 10px;              /* 按钮之间的间距 (可选，替代了原来的 margin) */
  margin: 10px 0;         /* 容器与上下元素的间距 (可选) */
}

canvas {
  max-width: 100%;
  height: auto;
  border: 1px solid #ccc;
}

.Prev-btn, .Next-btn,.Export-btn  {
  border: 1px solid #ccc; /* 添加边框 */
  padding: 5px 12px;
  font-size: 12px;
  color:rgb(24, 23, 23);

  border-radius: 5px;
  cursor: pointer;
  margin: 0 5px;
  background-color: #f9f9f9;
}
.result-header{
  background: linear-gradient(135deg, #4b5563, #1f2937);
  color: #e5e7eb;
  padding: 8px 16px;
  font-size: 0.9rem;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  flex-shrink: 0;}
.annotation-list{
  background-color: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  flex: 2;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许内容压缩 */}

</style>
