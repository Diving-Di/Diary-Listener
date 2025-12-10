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
          <div class="image-name" :title="item.image.split('/').pop()">
            {{ item.image.split('/').pop() }}
          </div>
          <div class="card-actions">
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

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  components: { IconPicture },
  props: ['token'],
  data() {
    return {
      images: [],
      loading: false,
      Delete
    }
  },
  watch: {
    token: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.fetchImages()
        } else {
          this.images = []
        }
      }
    }
  },
  methods: {
    async fetchImages() {
      if (!this.token) return
      this.loading = true
      try {
        const res = await axios.get(`${API}/images/`, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        this.images = res.data
      } catch (err) {
        console.error(err)
        ElMessage.error('获取图片失败')
      } finally {
        this.loading = false
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
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  margin-top: 20px;
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
  align-items: center;
  background-color: #fff;
}

.image-name {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}
</style>
