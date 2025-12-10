<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content container">
        <div class="logo">
          <el-icon :size="24" style="vertical-align: middle; margin-right: 8px"><Picture /></el-icon>
          <span>Image Manager</span>
        </div>
        <div v-if="token" class="user-info">
          <span class="welcome-text">Welcome, {{ username }}</span>
          <el-button type="danger" size="small" @click="logout" plain>Logout</el-button>
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
                  <el-input v-model="username" placeholder="Enter username" prefix-icon="User" />
                </el-form-item>
                <el-form-item label="Password">
                  <el-input v-model="password" type="password" placeholder="Enter password" prefix-icon="Lock" show-password />
                </el-form-item>
                <el-button type="primary" class="w-100" @click="login" :loading="loading">Login</el-button>
              </el-form>
            </el-tab-pane>
            
            <el-tab-pane label="Register" name="register">
              <el-form @submit.prevent="register" label-position="top">
                <el-form-item label="Username">
                  <el-input v-model="username" placeholder="Choose a username" prefix-icon="User" />
                </el-form-item>
                <el-form-item label="Email">
                  <el-input v-model="email" placeholder="Enter email" prefix-icon="Message" />
                </el-form-item>
                <el-form-item label="Password">
                  <el-input v-model="password" type="password" placeholder="Choose a password" prefix-icon="Lock" show-password />
                </el-form-item>
                <el-button type="success" class="w-100" @click="register" :loading="loading">Register</el-button>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>

      <div v-else>
        <el-card class="mb-20">
          <template #header>
            <div class="card-header">
              <span>上传新图片</span>
            </div>
          </template>
          <ImageUpload @uploaded="reload" :token="token" />
        </el-card>
        
        <Gallery ref="gallery" :token="token" />
      </div>
    </el-main>
  </el-container>
</template>

<script>
import axios from 'axios'
import { User, Lock, Message, Picture } from '@element-plus/icons-vue'
import ImageUpload from './components/ImageUpload.vue'
import Gallery from './components/Gallery.vue'
import { ElMessage } from 'element-plus'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  components: { ImageUpload, Gallery, User, Lock, Message, Picture },
  data() {
    return {
      view: 'login',
      username: '',
      password: '',
      email: '',
      token: localStorage.getItem('token') || null,
      loading: false
    }
  },
  methods: {
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
        ElMessage.success('登录成功')
      } catch (e) {
        ElMessage.error('登录失败：无效的凭据')
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
      this.username = ''
      this.password = ''
      ElMessage.info('Logged out')
    },
    reload() {
      this.$refs.gallery.fetchImages()
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
</style>
