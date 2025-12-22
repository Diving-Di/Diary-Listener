<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="24" style="vertical-align: middle; margin-right: 5px;"><Picture /></el-icon>
          <span>Image Manager</span>
        </div>
        <div v-if="token" class="user-info">
          <span class="welcome-text">欢迎登录, {{ displayUsername }}</span>
          <el-button type="danger" size="small" @click="logout" plain>退出登录</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="container">
      <div v-if="!token" class="auth-container">
        <el-card class="auth-card">
          <el-tabs v-model="view" stretch>
            <el-tab-pane label="Login" name="login">
              <el-form @submit.prevent="login" label-position="top">
                <el-form-item label="Username">
                  <el-input v-model="username" placeholder="请输入用户名" prefix-icon="User" />
                </el-form-item>
                <el-form-item label="Password">
                  <el-input v-model="password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
                </el-form-item>
                <el-button type="primary" class="w-100" @click="login" :loading="loading">登录</el-button>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="Register" name="register">
              <el-form @submit.prevent="register" label-position="top">
                <el-form-item label="Username">
                  <el-input v-model="username" placeholder="请输入用户名" prefix-icon="User" />
                </el-form-item>
                <el-form-item label="Email">
                  <el-input v-model="email" placeholder="请输入邮箱" prefix-icon="Message" />
                </el-form-item>
                <el-form-item label="Password">
                  <el-input v-model="password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
                </el-form-item>
                <el-button type="success" class="w-100" @click="register" :loading="loading">注册</el-button>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>

      <div v-else>
        <div class="top-row mb-20">
          <div class="upload-col">
            <el-card>
              <template #header>
                <div class="card-header">上传新图片</div>
              </template>
              <ImageUpload @uploaded="reload" :token="token" />
            </el-card>
          </div>

          <div class="carousel-col">
            <el-card>
              <div class="carousel-topbar">
                <el-button type="primary" plain @click="toggleCarouselEdit">
                  {{ editingCarousel ? '取消编辑' : '编辑轮播' }}
                </el-button>

                <el-button
                  v-if="editingCarousel"
                  type="primary"
                  @click="saveCarouselEdit"
                >
                  保存
                </el-button>
              </div>

              <div v-if="editingCarousel" class="carousel-editor">
                <div class="control-label">选择轮播图片（多选）</div>
                <el-select
                  v-model="carouselDraftIds"
                  multiple
                  filterable
                  clearable
                  placeholder="选择需要轮播的图片"
                  class="control-select"
                >
                  <el-option
                    v-for="img in imagesForCarousel"
                    :key="img.id"
                    :label="'图片 ' + img.id"
                    :value="img.id"
                  />
                </el-select>
              </div>

              <ImageCarousel :items="carouselItems" />

              <div class="search-area">
                <div class="control-label">按标签检索</div>
                <div class="search-row">
                  <el-select
                    v-model="filterTag"
                    clearable
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入后回车"
                    class="control-select"
                    @change="applyFilter"
                    @clear="applyFilter"
                  >
                    <el-option
                      v-for="name in availableTagNames"
                      :key="name"
                      :label="name"
                      :value="name"
                    />
                  </el-select>
                  <el-button class="search-btn" @click="applyFilter">检索</el-button>
                </div>
              </div>
            </el-card>
          </div>
        </div>

        <Gallery
          ref="gallery"
          :token="token"
          :filter-tag="filterTag"
          @images-changed="onImagesChanged"
        />
      </div>
    </el-main>
  </el-container>
</template>

<script>
import axios from 'axios'
import { User, Lock, Message, Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ImageUpload from './components/ImageUpload.vue'
import Gallery from './components/Gallery.vue'
import ImageCarousel from './components/ImageCarousel.vue'

const API = import.meta.env.VITE_API_BASE_URL || '/api'

function loadCarouselSelectedIdsSafe() {
  try {
    const raw = localStorage.getItem('carousel_selected_ids')
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch (e) {
    return []
  }
}

export default {
  components: { ImageUpload, Gallery, ImageCarousel, User, Lock, Message, Picture },
  data() {
    return {
      view: 'login',
      username: '',
      displayUsername: localStorage.getItem('username') || '',
      password: '',
      email: '',
      token: localStorage.getItem('token') || null,
      loading: false,

      filterTag: '',
      availableTagNames: [],

      imagesForCarousel: [],
      carouselSelectedIds: loadCarouselSelectedIdsSafe(),
      editingCarousel: false,
      carouselDraftIds: []
    }
  },
  computed: {
    carouselItems() {
      const selected = new Set(this.carouselSelectedIds || [])
      return (this.imagesForCarousel || []).filter(img => selected.has(img.id))
    }
  },
  watch: {
    token: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.fetchTags()
        } else {
          this.filterTag = ''
          this.availableTagNames = []
          this.imagesForCarousel = []
          this.carouselSelectedIds = []
          this.editingCarousel = false
          this.carouselDraftIds = []
          localStorage.removeItem('carousel_selected_ids')
        }
      }
    },
    carouselSelectedIds: {
      deep: true,
      handler(v) {
        localStorage.setItem('carousel_selected_ids', JSON.stringify(v || []))
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
              .filter(x => x.replace(/\s+/g, '') !== '["\"]')
          }
        } catch (e) {
          // fallthrough
          console.error(e)
        }
      }
      if (s.replace(/\s+/g, '') === '[]') return []
      if (s.replace(/\s+/g, '') === '["\"]') return []
      return [s]
    },
    async fetchTags() {
      if (!this.token) return
      try {
        const res = await axios.get(`${API}/tags/`, {
          headers: { Authorization: `Token ${this.token}` }
        })
        const names = (res.data || [])
          .filter(t => t && t.tag_type === 'Custom')
          .flatMap(t => this.normalizeTagNames(t && t.tag_name ? t.tag_name : ''))
        this.availableTagNames = Array.from(new Set(names))
      } catch (e) {
        console.error(e)
      }
    },
    applyFilter() {
      if (this.$refs.gallery && this.$refs.gallery.fetchImages) {
        this.$refs.gallery.fetchImages()
      }
    },
    onImagesChanged(images) {
      this.imagesForCarousel = Array.isArray(images) ? images : []
      const valid = new Set(this.imagesForCarousel.map(x => x && x.id).filter(Boolean))
      this.carouselSelectedIds = (this.carouselSelectedIds || []).filter(id => valid.has(id))
      this.carouselDraftIds = (this.carouselDraftIds || []).filter(id => valid.has(id))
    },
    toggleCarouselEdit() {
      if (!this.editingCarousel) {
        this.carouselDraftIds = [...(this.carouselSelectedIds || [])]
        this.editingCarousel = true
        return
      }
      this.editingCarousel = false
      this.carouselDraftIds = []
    },
    saveCarouselEdit() {
      this.carouselSelectedIds = [...(this.carouselDraftIds || [])]
      this.editingCarousel = false
      this.carouselDraftIds = []
    },
    async login() {
      if (!this.username || !this.password) {
        ElMessage.warning('请填写所有字段')
        return
      }
      this.loading = true
      try {
        const res = await axios.post(`${API}/login/`, {
          username: this.username,
          password: this.password
        })
        this.token = res.data.token
        localStorage.setItem('token', this.token)
        this.displayUsername = this.username
        localStorage.setItem('username', this.displayUsername)
        ElMessage.success('登录成功')
      } catch (e) {
        console.error(e)
        if (e.response) {
          ElMessage.error('登录失败：用户名或密码错误')
        } else if (e.request) {
          ElMessage.error('登录失败：无法连接到服务器，请检查网络或防火墙')
        } else {
          ElMessage.error('登录失败：' + e.message)
        }
      } finally {
        this.loading = false
      }
    },
    async register() {
      if (!this.username || !this.password || !this.email) {
        ElMessage.warning('请填写所有字段')
        return
      }
      this.loading = true
      try {
        await axios.post(`${API}/register/`, {
          username: this.username,
          password: this.password,
          email: this.email
        })
        ElMessage.success('注册成功，请登录。')
        this.view = 'login'
      } catch (e) {
        console.error(e)
        if (e.response && e.response.data) {
          ElMessage.error('注册失败：' + JSON.stringify(e.response.data))
        } else {
          ElMessage.error('注册失败：' + e.message)
        }
      } finally {
        this.loading = false
      }
    },
    logout() {
      this.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      this.username = ''
      this.displayUsername = ''
      this.password = ''
      ElMessage.info('退出登录成功')
    },
    reload() {
      if (this.$refs.gallery && this.$refs.gallery.fetchImages) {
        this.$refs.gallery.fetchImages()
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-text {
  font-size: 14px;
  color: #606266;
}

.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.auth-card {
  width: 100%;
  max-width: 400px;
}

.w-100 {
  width: 100%;
}

.card-header {
  font-weight: bold;
}

.top-row {
  display: flex;
  gap: 20px;
  align-items: stretch;
}

.upload-col {
  flex: 1;
  min-width: 0;
}

.carousel-col {
  flex: 1;
  min-width: 0;
}

.carousel-topbar {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 10px;
}

.carousel-editor {
  margin-bottom: 12px;
}

.control-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.control-select {
  width: 100%;
}

.search-area {
  margin-top: 12px;
  width: 100%;
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-btn {
  flex: none;
}

:deep(.upload-col .el-card),
:deep(.carousel-col .el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.upload-col .el-card__body),
:deep(.carousel-col .el-card__body) {
  flex: 1;
}

@media (max-width: 992px) {
  .top-row {
    flex-direction: column;
  }

  .search-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-btn {
    width: 100%;
  }
}
</style>
  align-items: center;

