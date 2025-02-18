<template>
  <div class="wsi-viewer">
    <div ref="container" class="viewer-container"></div>
    <div ref="overlay" 
         class="measurement-overlay" 
         :class="{ 'pan-mode': activeTool === 'pan' }"
         @mousedown.prevent="handleMouseDown"
         @mousemove.prevent="handleMouseMove"
         @mouseup.prevent="handleMouseUp"
         @mouseleave.prevent="handleMouseUp">
      <!-- 光标指示器 -->
      <div v-if="activeTool !== 'pan'" 
           class="cursor-indicator" 
           :style="cursorStyle"></div>
      <!-- 测量预览 -->
      <div v-if="isDrawing"
           :class="['measure-preview', activeTool + '-preview']"
           :style="drawingStyle">
        <template v-if="activeTool === 'distance'">
          <div class="line-body"></div>
          <div class="point start"></div>
          <div class="point end"></div>
        </template>
      </div>
      <!-- 已完成的测量 -->
      <div v-for="(mark, index) in measurements" 
           :key="'mark-' + index"
           :class="['measurement', mark.type]"
           :style="mark.style"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import OpenSeadragon from 'openseadragon'
import axios from 'axios'

const props = defineProps({
  slideUrl: String,
  activeTool: {
    type: String,
    default: 'pan'
  }
})

const emit = defineEmits(['measurement-complete', 'load-error'])

// Refs
const container = ref(null)
const overlay = ref(null)
const viewer = ref(null)
const isDrawing = ref(false)
const startPoint = ref(null)
const currentPoint = ref({ x: 0, y: 0 })
const measurements = ref([])

// Computed
const cursorStyle = computed(() => ({
  left: `${currentPoint.value.x}px`,
  top: `${currentPoint.value.y}px`
}))

const drawingStyle = computed(() => {
  if (!isDrawing.value || !startPoint.value) return {}

  const dx = currentPoint.value.x - startPoint.value.x
  const dy = currentPoint.value.y - startPoint.value.y

  if (props.activeTool === 'distance') {
    const length = Math.sqrt(dx * dx + dy * dy)
    const angle = Math.atan2(dy, dx) * (180 / Math.PI)
    return {
      left: `${startPoint.value.x}px`,
      top: `${startPoint.value.y}px`,
      width: `${length}px`,
      transform: `rotate(${angle}deg)`
    }
  }
  
  if (props.activeTool === 'area') {
    const width = Math.abs(dx)
    const height = Math.abs(dy)
    const left = Math.min(startPoint.value.x, currentPoint.value.x)
    const top = Math.min(startPoint.value.y, currentPoint.value.y)
    return {
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`
    }
  }
  
  return {}
})

// Helper functions
const getMeasurementStyle = (startPos, endPos, type) => {
  if (type === 'annotation') {
    return {
      left: `${startPos.x}px`,
      top: `${startPos.y}px`
    }
  }
  
  if (type === 'distance') {
    const dx = endPos.x - startPos.x
    const dy = endPos.y - startPos.y
    const length = Math.sqrt(dx * dx + dy * dy)
    const angle = Math.atan2(dy, dx) * (180 / Math.PI)
    return {
      left: `${startPos.x}px`,
      top: `${startPos.y}px`,
      width: `${length}px`,
      transform: `rotate(${angle}deg)`
    }
  }
  
  if (type === 'area') {
    const width = Math.abs(endPos.x - startPos.x)
    const height = Math.abs(endPos.y - startPos.y)
    const left = Math.min(startPos.x, endPos.x)
    const top = Math.min(startPos.y, endPos.y)
    return {
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`
    }
  }
}

const getMousePosition = (event) => {
  const rect = overlay.value.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
}

// Event handlers
const handleMouseDown = (event) => {
  if (!viewer.value || props.activeTool === 'pan') return
  console.log('Mouse down:', props.activeTool)
  
  const pos = getMousePosition(event)
  currentPoint.value = pos
  
  if (props.activeTool === 'annotation') {
    const viewerPoint = viewer.value.viewport.pointFromPixel(new OpenSeadragon.Point(pos.x, pos.y))
    const imagePoint = viewer.value.viewport.viewportToImageCoordinates(viewerPoint)
    
    measurements.value.push({
      type: 'annotation',
      style: {
        left: `${pos.x}px`,
        top: `${pos.y}px`
      }
    })
    
    emit('measurement-complete', {
      type: 'annotation',
      position: {
        x: Math.round(imagePoint.x),
        y: Math.round(imagePoint.y)
      }
    })
  } else {
    startPoint.value = pos
    isDrawing.value = true
  }
}

const handleMouseMove = (event) => {
  currentPoint.value = getMousePosition(event)
  
  if (isDrawing.value) {
    console.log('Drawing:', {
      start: startPoint.value,
      current: currentPoint.value,
      tool: props.activeTool
    })
  }
}

const handleMouseUp = (event) => {
  if (!isDrawing.value || !startPoint.value) return
  
  const endPos = getMousePosition(event)
  
  // Convert to image coordinates
  const startViewport = viewer.value.viewport.pointFromPixel(new OpenSeadragon.Point(startPoint.value.x, startPoint.value.y))
  const endViewport = viewer.value.viewport.pointFromPixel(new OpenSeadragon.Point(endPos.x, endPos.y))
  
  const startImage = viewer.value.viewport.viewportToImageCoordinates(startViewport)
  const endImage = viewer.value.viewport.viewportToImageCoordinates(endViewport)

  // Save measurement
  if (props.activeTool === 'distance') {
    const dx = endImage.x - startImage.x
    const dy = endImage.y - startImage.y
    const distance = Math.sqrt(dx * dx + dy * dy) * 0.2508
    
    measurements.value.push({
      type: 'distance',
      style: getMeasurementStyle(startPoint.value, endPos, 'distance')
    })
    
    emit('measurement-complete', {
      type: 'distance',
      value: distance,
      unit: 'μm'
    })
  } else if (props.activeTool === 'area') {
    const width = Math.abs(endImage.x - startImage.x)
    const height = Math.abs(endImage.y - startImage.y)
    const area = width * height * 0.2508 * 0.2508
    
    measurements.value.push({
      type: 'area',
      style: getMeasurementStyle(startPoint.value, endPos, 'area')
    })
    
    emit('measurement-complete', {
      type: 'area',
      value: area,
      unit: 'μm²'
    })
  }
  
  isDrawing.value = false
  startPoint.value = null
}

// Viewer initialization
const initViewer = async (slideId) => {
  try {
    console.log('初始化viewer:', slideId)
    const response = await axios.get(`/api/slides/${slideId}/info`)
    const info = response.data
    
    if (viewer.value) {
      viewer.value.destroy()
    }
    
    measurements.value = []
    viewer.value = new OpenSeadragon({
      element: container.value,
      prefixUrl: '/openseadragon/images/',
      showNavigator: true,
      navigatorPosition: 'BOTTOM_RIGHT',
      showRotationControl: true,
      
      // Performance settings
      minZoomImageRatio: 0.8,
      maxZoomPixelRatio: 2.5,
      visibilityRatio: 1,
      wrapHorizontal: false,
      wrapVertical: false,
      
      // Animation settings
      springStiffness: 10,
      animationTime: 0.5,
      
      // Mouse settings
      gestureSettingsMouse: {
        clickToZoom: false,
        dblClickToZoom: false,
        pinchToZoom: false,
        flickEnabled: false
      },
      
      // Tile settings
      tileSize: 256,
      minLevel: 0,
      maxLevel: info.level_count - 1,
      
      // Tile source
      tileSources: {
        width: info.dimensions[0],
        height: info.dimensions[1],
        tileSize: 256,
        minLevel: 0,
        maxLevel: info.level_count - 1,
        
        getLevelScale: (level) => {
          return 1 / (info.level_downsamples[level] || Math.pow(2, level))
        },
        
        getTileUrl: (level, x, y) => {
          return `/api/slides/${slideId}/tile?level=${level}&x=${x}&y=${y}&size=256`
        }
      }
    })

    // Wait for viewer to be ready
    viewer.value.addOnceHandler('open', () => {
      console.log('Viewer ready')
    })

    viewer.value.addOnceHandler('open-failed', () => {
      console.error('Viewer failed to open')
      emit('load-error', '加载切片失败')
    })

  } catch (error) {
    console.error('初始化失败:', error)
    emit('load-error', error.message)
  }
}

watch(() => props.slideUrl, (newUrl) => {
  if (newUrl) {
    initViewer(newUrl)
  } else if (viewer.value) {
    viewer.value.destroy()
    viewer.value = null
  }
}, { immediate: true })

watch(() => props.activeTool, (newTool) => {
  if (!viewer.value) return
  viewer.value.setMouseNavEnabled(newTool === 'pan')
})

onMounted(() => {
  if (props.slideUrl) {
    initViewer(props.slideUrl)
  }
})

onUnmounted(() => {
  if (viewer.value) {
    viewer.value.destroy()
  }
})

defineExpose({ clearMeasurements: () => measurements.value = [] })
</script>

<style lang="scss" scoped>
.wsi-viewer {
  width: 100%;
  height: 100%;
  position: relative;
  user-select: none;
}

.viewer-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: #f5f7fa;
}

.measurement-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  pointer-events: auto;
  
  &.pan-mode {
    pointer-events: none;
  }
}

.cursor-indicator {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid #ff3b3b;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 1001;
}

.measure-preview {
  position: absolute;
  pointer-events: none;
  z-index: 1002;
  transition: all 0.05s linear;

  &.distance-preview {
    height: 2px;
    transform-origin: left center;
    
    .line-body {
      position: absolute;
      left: 0;
      top: 50%;
      width: 100%;
      height: 2px;
      background-color: #ff3b3b;
      transform: translateY(-50%);
    }
    
    .point {
      position: absolute;
      width: 6px;
      height: 6px;
      background-color: #ff3b3b;
      border: 1px solid white;
      border-radius: 50%;
      transform: translate(-50%, -50%);
      
      &.start {
        left: 0;
        top: 50%;
      }
      
      &.end {
        right: 0;
        top: 50%;
        transform: translate(50%, -50%);
      }
    }
  }
  
  &.area-preview {
    border: 2px solid #ff3b3b;
    background-color: rgba(255, 59, 59, 0.15);
  }
}

.measurement {
  position: absolute;
  pointer-events: none;
  z-index: 1000;
  
  &.distance {
    height: 2px;
    background-color: #ff3b3b;
    transform-origin: left center;
    
    &::before,
    &::after {
      content: '';
      position: absolute;
      width: 6px;
      height: 6px;
      background-color: #ff3b3b;
      border: 1px solid white;
      border-radius: 50%;
    }
    
    &::before {
      left: 0;
      top: 50%;
      transform: translate(-50%, -50%);
    }
    
    &::after {
      right: 0;
      top: 50%;
      transform: translate(50%, -50%);
    }
  }
  
  &.area {
    border: 2px solid #ff3b3b;
    background-color: rgba(255, 59, 59, 0.15);
  }
  
  &.annotation {
    width: 10px;
    height: 10px;
    background-color: #ff3b3b;
    border: 2px solid white;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    animation: marker-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
}

@keyframes marker-pop {
  from {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
  }
  to {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
}
</style>