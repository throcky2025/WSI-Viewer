<template>
  <div class="app-container">
    <el-container>
      <el-header height="60px">
        <div class="header-content">
          <h1>CHIEF WSI查看器</h1>
          <el-upload
            class="slide-upload"
            action="/api/slides/upload"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :on-progress="handleUploadProgress"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            accept=".svs,.tif,.tiff"
          >
            <el-button type="primary" :loading="uploading">
              {{ uploading ? '正在上传...' : '打开切片' }}
            </el-button>
          </el-upload>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="250px">
          <div class="toolbar">
            <el-divider content-position="center">工具栏</el-divider>
            <el-radio-group v-model="activeTool" class="tool-group">
              <el-radio-button value="pan">
                <el-tooltip content="平移和缩放">
                  <div class="tool-button">
                    <el-icon><Aim /></el-icon>
                    <span>平移</span>
                  </div>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button value="distance">
                <el-tooltip content="测量距离">
                  <div class="tool-button">
                    <el-icon><ScaleToOriginal /></el-icon>
                    <span>测距</span>
                  </div>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button value="area">
                <el-tooltip content="测量面积">
                  <div class="tool-button">
                    <el-icon><Position /></el-icon>
                    <span>面积</span>
                  </div>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button value="annotation">
                <el-tooltip content="添加标注">
                  <div class="tool-button">
                    <el-icon><Place /></el-icon>
                    <span>标注</span>
                  </div>
                </el-tooltip>
              </el-radio-button>
            </el-radio-group>

            <el-divider content-position="center">测量结果</el-divider>
            <div class="measurement-results">
              <el-table v-if="measurements.length" :data="measurements" style="width: 100%" height="300">
                <el-table-column prop="type" label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getMeasurementTagType(row.type)" size="small">
                      {{ getMeasurementTypeLabel(row.type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="value" label="数值">
                  <template #default="{ row }">
                    {{ formatMeasurementValue(row) }}
                  </template>
                </el-table-column>
                <el-table-column width="50">
                  <template #default="scope">
                    <el-button
                      type="danger"
                      size="small"
                      circle
                      @click="deleteMeasurement(scope.$index)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <el-empty v-else description="暂无测量数据" />

              <div v-if="measurements.length" class="action-buttons">
                <el-button type="danger" size="small" @click="clearMeasurements">
                  清除所有
                </el-button>
                <el-button type="primary" size="small" @click="exportMeasurements">
                  导出
                </el-button>
              </div>
            </div>
          </div>
        </el-aside>

        <el-main>
          <div v-if="currentSlide" class="viewer-container">
            <WSIViewer
              ref="wsiViewer"
              :slide-url="currentSlide"
              :active-tool="activeTool"
              @measurement-complete="handleMeasurementComplete"
              @load-error="handleViewerError"
            />
          </div>
          <div v-else class="empty-viewer">
            <div class="upload-placeholder">
              <el-empty :description="uploading ? '正在上传文件...' : '请选择要查看的切片文件'" />
              <el-progress 
                v-if="uploading"
                :percentage="uploadProgress"
                :status="uploadProgress === 100 ? 'success' : ''"
              />
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Aim, ScaleToOriginal, Position, Place } from '@element-plus/icons-vue'
import WSIViewer from './components/WSIViewer.vue'

// 状态管理
const currentSlide = ref(null)
const activeTool = ref('pan')
const wsiViewer = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const measurements = ref([])

// 工具类型标签
const getMeasurementTagType = (type) => {
  switch (type) {
    case 'distance': return 'primary'
    case 'area': return 'success'
    case 'annotation': return 'warning'
    default: return 'info'
  }
}

const getMeasurementTypeLabel = (type) => {
  switch (type) {
    case 'distance': return '距离'
    case 'area': return '面积'
    case 'annotation': return '标注'
    default: return '未知'
  }
}

// 格式化测量值
const formatMeasurementValue = (measurement) => {
  if (measurement.type === 'annotation') {
    return `(${measurement.position.x}, ${measurement.position.y})`
  } else {
    return `${measurement.value.toFixed(2)} ${measurement.unit}`
  }
}

// 文件上传处理
const beforeUpload = (file) => {
  console.log('准备上传文件:', file.name)
  const isValidType = ['.svs', '.tif', '.tiff'].some(ext => 
    file.name.toLowerCase().endsWith(ext)
  )
  if (!isValidType) {
    ElMessage.error('只支持.svs、.tif、.tiff格式的切片文件')
    return false
  }
  
  uploading.value = true
  uploadProgress.value = 0
  currentSlide.value = null
  measurements.value = []
  
  return true
}

const handleUploadProgress = (event) => {
  uploadProgress.value = Math.round(event.percent)
}

const handleUploadSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 100
  
  if (response.success) {
    currentSlide.value = response.slideId
    ElMessage.success('切片加载成功')
  } else {
    currentSlide.value = null
    ElMessage.error(response.message || '切片加载失败')
  }
}

const handleUploadError = (error) => {
  uploading.value = false
  uploadProgress.value = 0
  currentSlide.value = null
  
  let errorMsg = '文件上传失败'
  if (error.response?.data?.detail) {
    errorMsg = error.response.data.detail
  }
  ElMessage.error(errorMsg)
}

// 测量结果处理
const handleMeasurementComplete = (measurement) => {
  console.log('新的测量结果:', measurement)
  measurements.value = [
    ...measurements.value,
    {
      id: Date.now(),
      ...measurement
    }
  ]
}

const deleteMeasurement = (index) => {
  measurements.value = measurements.value.filter((_, i) => i !== index)
}

const clearMeasurements = () => {
  measurements.value = []
  wsiViewer.value?.clearMeasurements()
}

// 导出测量结果
const exportMeasurements = () => {
  const formatValue = (m) => {
    if (m.type === 'annotation') {
      return `(${m.position.x}, ${m.position.y})`
    }
    return `${m.value.toFixed(2)} ${m.unit}`
  }

  const csv = [
    ['类型', '数值', '时间'].join(','),
    ...measurements.value.map(m => [
      getMeasurementTypeLabel(m.type),
      formatValue(m),
      new Date(m.id).toLocaleString()
    ].join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `measurements_${new Date().toISOString()}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

const handleViewerError = (error) => {
  console.error('查看器错误:', error)
  ElMessage.error('加载切片失败: ' + error)
}
</script>

<style lang="scss">
.app-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  
  /* 使用系统默认字体 */
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
               'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 
               'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
               'Noto Color Emoji';
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;

  h1 {
    margin: 0;
    font-size: 20px;
    color: #333;
  }
}

.toolbar {
  padding: 20px;

  .tool-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;

    :deep(.el-radio-button__inner) {
      width: 100%;
      text-align: center;
      border-radius: 4px;
      border: 1px solid #dcdfe6;
      
      &:hover {
        color: var(--el-color-primary);
      }
    }

    .el-radio-button:first-child .el-radio-button__inner {
      border-radius: 4px;
    }

    .el-radio-button:last-child .el-radio-button__inner {
      border-radius: 4px;
    }
  }

  .tool-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    padding: 8px 0;
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
  }
}

.measurement-results {
  margin-top: 10px;
  
  .el-table {
    margin-bottom: 10px;
  }
}

.viewer-container {
  height: 100%;
  background-color: #f5f7fa;
}

.empty-viewer {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  
  .upload-placeholder {
    text-align: center;
    
    .el-progress {
      width: 200px;
      margin-top: 20px;
    }
  }
}

:deep(.el-main) {
  padding: 0;
}
</style>