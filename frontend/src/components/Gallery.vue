<template>
  <div v-loading="loading">
    <el-empty v-if="!loading && images.length === 0" description="未找到图片" />
    
    <div v-else class="gallery-grid">
      <el-card 
        v-for="item in images" 
        :key="item.id" 
        :body-style="{ padding: '0px' }" 
        shadow="hover"
        class="gallery-item"
      >
        <div class="image-wrapper">
          <el-image 
            :src="getFullUrl(item.thumbnail || item.image)" 
            :preview-src-list="[getFullUrl(item.image)]"
            fit="cover"
            class="gallery-image"
            loading="lazy"
            preview-teleported
          >
            <template #error>
              <div class="image-slot">
                <el-icon><icon-picture /></el-icon>
              </div>
            </template>
          </el-image>
        </div>
        <div class="card-content">
          <div class="card-left">
            <div class="image-name" :title="item.image.split('/').pop()">
              {{ item.image.split('/').pop() }}
            </div>

            <div v-if="(customTags(item).length) || (aiTags(item).length) || item.exif_datetime || item.created || item.location || item.resolution" class="meta-area">
              <div v-if="customTags(item).length" class="tag-list">
                <el-tag
                  v-for="t in customTags(item)"
                  :key="t.id || t.tag_name"
                  size="small"
                  class="tag-item"
                >
                  {{ t.tag_name }}
                </el-tag>
              </div>

              <div v-if="aiTags(item).length" class="tag-list">
                <el-tag
                  v-for="t in aiTags(item)"
                  :key="'ai-' + (t.id || t.tag_name)"
                  size="small"
                  type="success"
                  class="tag-item"
                >
                  AI: {{ t.tag_name }}
                </el-tag>
              </div>
              <div v-if="item.exif_datetime" class="meta-line">拍摄时间：{{ formatDate(item.exif_datetime) }}</div>
              <div v-else-if="item.created" class="meta-line">上传时间：{{ formatDate(item.created) }}</div>
              <div v-if="item.location" class="meta-line">地点：{{ item.location }}</div>
              <div v-if="item.resolution" class="meta-line">分辨率：{{ item.resolution }}</div>

              <div class="edit-tags">
                <el-select
                  v-model="editTagNames[item.id]"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="为该图片添加自定义标签"
                  size="small"
                  class="edit-tag-select"
                >
                  <el-option
                    v-for="name in availableTagNames"
                    :key="name"
                    :label="name"
                    :value="name"
                  />
                </el-select>
                <el-button
                  size="small"
                  type="primary"
                  :loading="saving[item.id]"
                  @click="saveTags(item)"
                >
                  保存
                </el-button>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <el-button
              type="success"
              circle
              size="small"
              :loading="aiLoading[item.id]"
              @click="aiTag(item)"
              title="AI生成标签"
            >AI</el-button>
            <el-button type="danger" :icon="Delete" circle size="small" @click="remove(item.id)" />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { Delete, Picture as IconPicture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const API = import.meta.env.VITE_API_BASE_URL || '/api'
// const API = 'http://192.168.226.224:8000/api'

export default {
  components: { IconPicture },
  props: {
    token: String,
    filterTag: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      images: [],
      loading: false,
      Delete,
      availableTagNames: [],
      editTagNames: {},
      saving: {},
      aiLoading: {}
    }
  },
  watch: {
    token: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.fetchTags()
          this.fetchImages()
        } else {
          this.images = []
          this.$emit('images-changed', [])
          this.availableTagNames = []
          this.editTagNames = {}
        }
      }
    },
    filterTag: {
      handler() {
        if (this.token) {
          this.fetchImages()
        }
      }
    }
  },
  methods: {
    normalizeTagNames(raw) {
      if (raw === null || raw === undefined) return []
      const s = String(raw).trim()
      if (!s) return []

      // If user mistakenly saved a JSON array string (e.g. ["风景"]) treat it as list.
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
          .filter(t => t && t.tag_type === 'Custom')
          .flatMap(t => this.normalizeTagNames(t && t.tag_name ? t.tag_name : ''))
        this.availableTagNames = Array.from(new Set(names))
      } catch (err) {
        console.error(err)
      }
    },
    customTags(item) {
      const tags = (item && item.tags) ? item.tags : []
      const seen = new Set()
      const result = []
      for (const t of tags) {
        // 只展示自定义标签，避免 EXIF 标签与下方元信息重复
        if (t && t.tag_type && t.tag_type !== 'Custom') continue
        const names = this.normalizeTagNames(t && t.tag_name ? t.tag_name : '')
        for (const name of names) {
          if (seen.has(name)) continue
          seen.add(name)
          result.push({ ...t, tag_name: name })
        }
      }
      return result
    },

    aiTags(item) {
      const tags = (item && item.tags) ? item.tags : []
      const seen = new Set()
      const result = []
      for (const t of tags) {
        if (!t || t.tag_type !== 'AI') continue
        const name = (t.tag_name || '').toString().trim()
        if (!name) continue
        if (seen.has(name)) continue
        seen.add(name)
        result.push({ ...t, tag_name: name })
      }
      return result
    },
    formatDate(v) {
      if (!v) return ''
      try {
        const d = new Date(v)
        if (Number.isNaN(d.getTime())) return String(v)
        return d.toLocaleString()
      } catch (e) {
        return String(v)
      }
    },
    async fetchImages() {
      if (!this.token) return
      this.loading = true
      try {
        const params = {}
        if (this.filterTag && String(this.filterTag).trim()) {
          params.tag = String(this.filterTag).trim()
        }
        const res = await axios.get(`${API}/images/`, {
          headers: { 'Authorization': `Token ${this.token}` },
          params
        })
        this.images = res.data
        this.$emit('images-changed', this.images)

        // 初始化每张图片的编辑标签（仅自定义标签）
        const nextEdit = { ...this.editTagNames }
        for (const item of this.images || []) {
          if (!item || !item.id) continue
          const current = this.customTags(item).map(t => t.tag_name)
          if (!Array.isArray(nextEdit[item.id])) {
            nextEdit[item.id] = current
          }
        }
        this.editTagNames = nextEdit
      } catch (err) {
        console.error(err)
        ElMessage.error('获取图片失败')
      } finally {
        this.loading = false
      }
    },

    async saveTags(item) {
      if (!item || !item.id) return
      if (!this.token) return

      const raw = this.editTagNames[item.id] || []
      const cleaned = raw
        .map(s => String(s).trim())
        .filter(Boolean)
        .filter(s => s.replace(/\s+/g, '') !== '[]')

      this.saving = { ...this.saving, [item.id]: true }
      try {
        const form = new FormData()
        form.append('tag_names', JSON.stringify(cleaned))
        await axios.patch(`${API}/images/${item.id}/`, form, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        ElMessage.success('标签已更新')
        await Promise.all([this.fetchTags(), this.fetchImages()])
      } catch (err) {
        console.error(err)
        ElMessage.error('标签更新失败')
      } finally {
        this.saving = { ...this.saving, [item.id]: false }
      }
    },
    async remove(id) {
      try {
        await ElMessageBox.confirm(
          '你想要删除这张图片吗？',
          '警告',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        await axios.delete(`${API}/images/${id}/`, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        ElMessage.success('图片已删除')
        this.fetchImages()
      } catch (err) {
        if (err !== 'cancel') {
          console.error(err)
          ElMessage.error('图片删除失败')
        }
      }
    },

    async aiTag(item) {
      if (!item || !item.id) return
      if (!this.token) return
      this.aiLoading = { ...this.aiLoading, [item.id]: true }
      try {
        await axios.post(`${API}/images/${item.id}/ai_tag/`, null, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        ElMessage.success('AI标签已生成')
        await this.fetchImages()
      } catch (err) {
        console.error(err)
        const msg = err.response?.data?.detail || 'AI标签生成失败（可检查是否配置AI密钥）'
        ElMessage.error(msg)
      } finally {
        this.aiLoading = { ...this.aiLoading, [item.id]: false }
      }
    },
    getFullUrl(url) {
      if (!url) return ''
      if (url.startsWith('http') || url.startsWith('https')) {
        return url
      }
      const baseUrl = API.replace(/\/api\/?$/, '')
      return `${baseUrl}${url}`
    }
  }
}
</script>

<style scoped>
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
  margin-top: 20px;
}

@media (max-width: 1200px) {
  .gallery-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 992px) {
  .gallery-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .gallery-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .image-wrapper {
    height: 160px;
  }
}

.gallery-item {
  width: 100%;
}

.image-wrapper {
  height: 220px;
  overflow: hidden;
  background-color: #f5f7fa;
  display: flex;
  justify-content: center;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}

.gallery-image {
  width: 100%;
  height: 100%;
  display: block;
  transition: transform 0.3s;
}

.gallery-image:hover {
  transform: scale(1.05);
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
  font-size: 30px;
}

.card-content {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background-color: #fff;
}

.card-left {
  min-width: 0;
  flex: 1;
}

.image-name {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.meta-area {
  margin-top: 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.tag-item {
  max-width: 180px;
}

.meta-line {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.edit-tags {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-tag-select {
  flex: 1;
  min-width: 140px;
}
</style>
