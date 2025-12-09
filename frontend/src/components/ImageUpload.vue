<template>
  <div>
    <input type="file" @change="onFileChange" accept="image/*" />
    <button class="btn" @click="upload" :disabled="!file">上传</button>
    <span v-if="loading"> 上传中...</span>
  </div>
</template>

<script>
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  props: ['token'],
  data() {
    return {
      file: null,
      loading: false
    }
  },
  methods: {
    onFileChange(e) {
      this.file = e.target.files[0]
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
        this.file = null
        this.$el.querySelector('input[type=file]').value = ''
      } catch (err) {
        console.error(err)
        alert('上传失败')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
