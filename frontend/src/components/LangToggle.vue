<script setup lang="ts">
import { useI18n, type Locale } from '@/i18n'

const { locale } = useI18n()

const locales: { value: Locale; label: string }[] = [
  { value: 'zh-CN', label: '中' },
  { value: 'en-US', label: 'EN' },
]

function toggle() {
  locale.value = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
}
</script>

<template>
  <div class="flex items-center gap-0.5">
    <button
      v-for="l in locales"
      :key="l.value"
      @click="toggle"
      class="px-1.5 py-0.5 text-[10px] rounded transition-colors font-medium"
      :class="locale === l.value ? 'bg-indigo-600 text-white' : 'text-white/50 hover:text-white/70'"
    >
      {{ l.label }}
    </button>
  </div>
</template>
