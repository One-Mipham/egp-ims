<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-wrench text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">{{ route.meta.pageTitle || '功能开发中' }}</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
