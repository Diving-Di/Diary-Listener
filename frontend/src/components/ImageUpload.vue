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

    <div class="tag-area">
      <div class="tag-label">自定义标签（可多选/可输入）</div>
      <el-select
        v-model="tagNames"
        multiple
        filterable
        allow-create
        default-first-option
        placeholder="输入标签后回车，或从下拉中选择"
        class="tag-select"
      >
        <el-option
          v-for="name in availableTagNames"
          :key="name"
          :label="name"
          :value="name"
        />
      </el-select>
    </div>

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

const API = import.meta.env.VITE_API_BASE_URL || '/api'
// const API = 'http://192.168.226.224:8000/api'

export default {
  components: { UploadFilled, Document },
  props: ['token'],
  data() {
    return {
      fileList: [],
      loading: false,
      tagNames: [],
      availableTagNames: []
    }
  },
  watch: {
    token: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.fetchTags()
        } else {
          this.availableTagNames = []
          this.tagNames = []
        }
      }
    }
  },
  methods: {
    normalizeTagNames(raw) {
      if (raw === null || raw === undefined) return []
      const s = String(raw).trim()
      if (!s) return []
      if (s.startsWith('[') && s.endsWith(']')) {
        try {
          const parsed = JSON.parse(s)
          if (Array.isArray(parsed)) {
            return parsed
              .map(x => (x === null || x === undefined) ? '' : String(x).trim())
              .filter(Boolean)
              .filter(x => x.replace(/\s+/g, '') !== '[]')
              .filter(x => x.replace(/\s+/g, '') !== '[""]')
          }
        } catch (e) {
          // fallthrough
        }
      }
      if (s.replace(/\s+/g, '') === '[]') return []
      if (s.replace(/\s+/g, '') === '[""]') return []
      return [s]
    },
    async fetchTags() {
      if (!this.token) return
      try {
        const res = await axios.get(`${API}/tags/`, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        const names = (res.data || [])
          // 这里只作为“自定义标签”的可选项：过滤掉自动生成的 EXIF 标签
          .filter(t => t && t.tag_type === 'Custom')
          .flatMap(t => this.normalizeTagNames(t && t.tag_name ? t.tag_name : ''))
        this.availableTagNames = Array.from(new Set(names))
      } catch (err) {
        console.error(err)
        // 标签获取失败不影响上传
      }
    },
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
        // 不加标签时也显式提交空数组，避免沿用上次标签的误解
        const cleaned = (this.tagNames || []).flatMap(x => this.normalizeTagNames(x))
        form.append('tag_names', JSON.stringify(cleaned))
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
        // 上传成功：清空已选标签（不加标签就为空）
        this.tagNames = []
        this.fetchTags()
      }
      
      this.loading = false
    }
  }
}
</script>

<style scoped>
.upload-container {
  width: 100%;
  box-sizing: border-box;
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
  align-items: center;
  justify-content: center;
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

.tag-area {
  margin-top: 12px;
  text-align: left;
}

.tag-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.tag-select {
  width: 100%;
}
</style>
