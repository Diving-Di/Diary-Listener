<template>
  <div class="upload-container">
    <el-upload
      class="upload-demo"
      drag
      action="#"
      multiple
      :auto-upload="false"
      :file-list="fileList"
      :on-change="handleChange"
      :on-remove="handleRemove"
      :show-file-list="true"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
    </el-upload>

    <div v-if="fileList.length > 0" class="actions-area">
      <el-button type="primary" @click="upload" :loading="loading">
        开始上传 ({{ fileList.length }})
      </el-button>
      <el-button @click="fileList = []" :disabled="loading">清空</el-button>
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
      fileList: [],
      loading: false
    }
  },
  methods: {
    handleChange(uploadFile, uploadFiles) {
      this.fileList = uploadFiles
    },
    handleRemove(uploadFile, uploadFiles) {
      this.fileList = uploadFiles
    },
    async upload() {
      if (this.fileList.length === 0) return
      
      this.loading = true
      let successCount = 0
      let failCount = 0
      
      const promises = this.fileList.map(async (file) => {
        const form = new FormData()
        form.append('image', file.raw)
        try {
          await axios.post(`${API}/images/`, form, {
            headers: { 
              'Content-Type': 'multipart/form-data',
              'Authorization': `Token ${this.token}`
            }
          })
          successCount++
        } catch (err) {
          console.error(err)
          failCount++
        }
      })

      await Promise.all(promises)
      
      if (successCount > 0) {
        ElMessage.success(`成功上传 ${successCount} 张图片`)
        this.$emit('uploaded')
      }
      
      if (failCount > 0) {
        ElMessage.error(`${failCount} 张图片上传失败`)
      } else {
        this.fileList = []
      }
      
      this.loading = false
    }
  }
}
</script>

<style scoped>
.upload-container {
  width: 800pt;
  text-align: center;
  padding: 10px;
}

.upload-demo {
  width: 100%;
}

.upload-demo :deep(.el-upload) {
  width: 100%;
  display: block;
}

.upload-demo :deep(.el-upload-dragger) {
  width: 100%;
  padding: 20px;
  height: 140px;
  display: flex;
  flex-direction: column;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  transition: border-color 0.3s;
  box-sizing: border-box;
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

.actions-area {
  margin-top: 15px;
  display: flex;
  justify-content: center;
  gap: 15px;
}
</style>
