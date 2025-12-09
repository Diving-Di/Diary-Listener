<template>
  <div class="container">
    <h1>Image Manager</h1>
    
    <div v-if="!token">
      <div class="tabs">
        <button @click="view = 'login'" :class="{active: view === 'login'}">Login</button>
        <button @click="view = 'register'" :class="{active: view === 'register'}">Register</button>
      </div>
      
      <div v-if="view === 'login'" class="auth-form">
        <h2>Login</h2>
        <input v-model="username" placeholder="Username" />
        <input v-model="password" type="password" placeholder="Password" />
        <button @click="login">Login</button>
      </div>
      
      <div v-if="view === 'register'" class="auth-form">
        <h2>Register</h2>
        <input v-model="username" placeholder="Username" />
        <input v-model="email" placeholder="Email" />
        <input v-model="password" type="password" placeholder="Password" />
        <button @click="register">Register</button>
      </div>
    </div>

    <div v-else>
      <div class="header">
        <span>Welcome, {{ username }}</span>
        <button @click="logout">Logout</button>
      </div>
      <div class="controls">
        <ImageUpload @uploaded="reload" :token="token" />
      </div>
      <Gallery ref="gallery" :token="token" />
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ImageUpload from './components/ImageUpload.vue'
import Gallery from './components/Gallery.vue'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  components: { ImageUpload, Gallery },
  data() {
    return {
      view: 'login',
      username: '',
      password: '',
      email: '',
      token: localStorage.getItem('token') || null
    }
  },
  methods: {
    async login() {
      try {
        const res = await axios.post(`${API}/login/`, {
          username: this.username,
          password: this.password
        })
        this.token = res.data.token
        localStorage.setItem('token', this.token)
      } catch (e) {
        alert('Login failed')
      }
    },
    async register() {
      try {
        await axios.post(`${API}/register/`, {
          username: this.username,
          password: this.password,
          email: this.email
        })
        alert('Registered successfully. Please login.')
        this.view = 'login'
      } catch (e) {
        console.error(e)
        if (e.response && e.response.data) {
          alert('Registration failed: ' + JSON.stringify(e.response.data))
        } else {
          alert('Registration failed: ' + e.message)
        }
      }
    },
    logout() {
      this.token = null
      localStorage.removeItem('token')
      this.username = ''
      this.password = ''
    },
    reload() {
      this.$refs.gallery.fetchImages()
    }
  }
}
</script>

<style scoped>
.container { max-width: 800px; margin: 0 auto; padding: 20px; }
.tabs { margin-bottom: 20px; }
.tabs button { margin-right: 10px; padding: 5px 10px; }
.tabs button.active { font-weight: bold; border-bottom: 2px solid #333; }
.auth-form { display: flex; flex-direction: column; gap: 10px; max-width: 300px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h1 { margin-bottom: 12px; }
</style>
