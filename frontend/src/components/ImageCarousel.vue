<template>
  <div class="carousel-wrap">
    <el-empty v-if="!items || items.length === 0" description="未选择轮播图片" />

    <el-carousel
      v-else
      height="200px"
      indicator-position="outside"
    >
      <el-carousel-item v-for="item in items" :key="item.id">
        <el-image
          :src="getFullUrl(item.image)"
          fit="contain"
          class="carousel-image"
          loading="lazy"
          preview-teleported
          :preview-src-list="[getFullUrl(item.image)]"
        >
          <template #error>
            <div class="image-slot">图片加载失败</div>
          </template>
        </el-image>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<script>
const API = import.meta.env.VITE_API_BASE_URL || '/api'

export default {
  name: 'ImageCarousel',
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  methods: {
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
.carousel-wrap {
  width: 100%;
}

.carousel-image {
  width: 100%;
  height: 200px;
}

.image-slot {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  background: #f5f7fa;
}
</style>
