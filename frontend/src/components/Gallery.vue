<template>
  <div>
    <div v-if="loading">加载中...</div>
    <div v-else class="grid">
      <div v-for="item in images" :key="item.id" class="card">
        <img :src="item.thumbnail || item.image" class="thumb" />
        <div style="margin-top:8px">{{ item.image.split('/').pop() }}</div>
        <div style="margin-top:6px">
          <button class="btn btn-danger" @click="remove(item.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default {
  props: ['token'],
  data() {
    return {
      images: [],
      loading: false
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
        alert('获取图片失败')
      } finally {
        this.loading = false
      }
    },
    async remove(id) {
      if (!confirm('确定删除这张图片吗？')) return
      try {
        await axios.delete(`${API}/images/${id}/`, {
          headers: { 'Authorization': `Token ${this.token}` }
        })
        this.fetchImages()
      } catch (err) {
        console.error(err)
        alert('删除失败')
      }
    }
  }
}
</script>
