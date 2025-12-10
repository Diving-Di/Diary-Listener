<template>
  <div class="upload-container">
    <el-upload
      class="upload-demo"
      drag
      action="#"
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
    </el-upload>

    <div v-if="file" class="preview-area">
      <div class="file-info">
        <el-icon><Document /></el-icon>
        <span>{{ file.name }}</span>
      </div>
      <el-button type="primary" @click="upload" :loading="loading">
        开始上传
      </el-button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  components: { UploadFilled, Document },
  props: ['token'],
  data() {
    return {
      file: null,
      loading: false
    }
  },
  methods: {
    handleFileChange(uploadFile) {
      this.file = uploadFile.raw
    },
    async upload() {
      if (!this.file) return
      const form = new FormData()
      form.append('image', this.file)
      this.loading = true
      try {
        await axios.post(`${API}/images/`, form, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            'Authorization': `Token ${this.token}`
          }
        })
        this.$emit('uploaded')
        ElMessage.success('图片上传成功')
        this.file = null
      } catch (err) {
        console.error(err)
        ElMessage.error('上传失败')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.upload-container {
  text-align: center;
  padding: 10px;
}

.upload-demo :deep(.el-upload-dragger) {
  padding: 20px;
  height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  transition: border-color 0.3s;
}

.upload-demo :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.el-icon--upload {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}

.el-upload__text {
  font-size: 14px;
  color: #606266;
}

.el-upload__text em {
  color: #409eff;
  font-weight: bold;
}

.preview-area {
  margin-top: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}
</style>
