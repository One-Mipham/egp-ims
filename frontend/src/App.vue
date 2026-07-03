<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMe } from '@/api'

import SidebarMenu from '@/components/SidebarMenu.vue'
import LangToggle from '@/components/LangToggle.vue'
import { menuSections, flattenItems } from '@/config/menuConfig'
import { useI18n } from '@/i18n'

const { t, locale } = useI18n()

const route = useRoute()
const router = useRouter()
const currentUser = ref<{ username: string; role: string } | null>(null)

const isLoginPage = computed(() => ['/login', '/register'].includes(route.path))

const menuItems = flattenItems(menuSections)

// Toast notification
const notificationMessage = ref<string | null>(null)
let notificationTimer: ReturnType<typeof setTimeout> | null = null

function showNotification(msg: string) {
  notificationMessage.value = msg
  if (notificationTimer) clearTimeout(notificationTimer)
  notificationTimer = setTimeout(() => {
    notificationMessage.value = null
  }, 3000)
}

const THEMES = [
  { id: 'classic', name: '墨绿经典', swatch: ['#1a3525', '#6ee7b0', '#991B1B'] },
  { id: 'light',   name: '极简亮色', swatch: ['#24292f', '#79c0ff', '#cf222e'] },
  { id: 'dark',    name: '深邃暗色', swatch: ['#0d1117', '#58a6ff', '#f85149'] },
  { id: 'blue',    name: '蓝调专业', swatch: ['#1a2744', '#fbbf24', '#d97706'] },
  { id: 'contrast',name: '高对比度', swatch: ['#000000', '#ffff00', '#cc0000'] },
]
const currentTheme = ref(localStorage.getItem('theme') || 'classic')
const showThemePopup = ref(false)

function applyTheme(id: string) {
  currentTheme.value = id
  localStorage.setItem('theme', id)
  document.documentElement.setAttribute('data-theme', id)
  if (id === 'dark') {
    document.documentElement.classList.add('p-dark')
  } else {
    document.documentElement.classList.remove('p-dark')
  }
  showThemePopup.value = false
}

function initTheme() {
  applyTheme(currentTheme.value)
}

const ROLE_LABELS: Record<string, string> = {
  cashier: '出纳',
  accountant: '会计',
  finance_manager: '财务经理',
  finance_director: '财务总监',
  super_admin: '超级管理员',
}

async function loadCurrentUser() {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }
  try {
    const res = await getMe()
    currentUser.value = res.data
  } catch {
    localStorage.removeItem('token')
    router.push('/login')
  }
}

onMounted(async () => {
  initTheme()
  document.addEventListener('click', (e) => {
    if (showThemePopup.value && !(e.target as HTMLElement).closest('.theme-switcher')) {
      showThemePopup.value = false
    }
  })
  if (isLoginPage.value) return
  await loadCurrentUser()
})

// 登录成功后从 /login → / 切换时，App.vue 不会重新挂载，
// onMounted 不会再次执行，导致 currentUser 保持 null，
// SidebarMenu 拿不到 role，只显示"知识库"。
// 通过 watch 检测从登录页到认证页的转换，触发加载。
watch(isLoginPage, async (nowLogin) => {
  if (!nowLogin) {
    await loadCurrentUser()
  }
})

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <!-- Login page: no layout -->
  <router-view v-if="isLoginPage" />

  <!-- App layout for authenticated pages -->
  <div v-else class="flex h-screen bg-stone-50">
    <!-- Sidebar: deep green -->
    <aside class="sidebar w-[340px] text-white flex flex-col shrink-0 no-print">
      <!-- Header -->
	      <div class="h-10 flex items-center px-3 sidebar-header shrink-0 gap-2">
        <img src="/company-logo.jpg" alt="MiphamAI" class="h-5 w-auto rounded-sm" />
	        <span class="ml-2 text-xs font-medium tracking-wider sidebar-header-text">{{ t("app.brand") }}</span>
	        <div v-if="locale !== 'en-US'" class="ml-auto"><LangToggle /></div>
      </div>

      <!-- Scrolling banner -->
      <div class="overflow-hidden sidebar-banner h-6 shrink-0 flex items-center">
        <div class="marquee-text whitespace-nowrap text-[10px] sidebar-banner-text font-medium">
          One Mipham Corporation 技术支持 &nbsp;&nbsp;&nbsp; One Mipham Corporation 技术支持 &nbsp;&nbsp;&nbsp; One Mipham Corporation 技术支持
        </div>
      </div>

      <!-- Navigation -->
      <SidebarMenu
        :sections="menuSections"
        :user-role="currentUser?.role || ''"
        @locked="showNotification"
      />

      <!-- Theme switcher -->
      <div class="relative theme-switcher shrink-0">
        <button @click="showThemePopup = !showThemePopup" class="theme-switcher-btn">
          <span class="w-3 h-3 rounded-full" :style="{ background: THEMES.find(t => t.id === currentTheme)?.swatch[1] || '#6ee7b0' }" />
          <span class="flex-1 text-left">{{ THEMES.find(t => t.id === currentTheme)?.name || '经典' }}</span>
          <i class="pi pi-chevron-up text-[9px] transition-transform" :style="{ transform: showThemePopup ? 'rotate(0deg)' : 'rotate(180deg)' }" />
        </button>
        <div v-if="showThemePopup" class="theme-popup">
          <button v-for="t in THEMES" :key="t.id" :class="['theme-option', { active: currentTheme === t.id }]" @click="applyTheme(t.id)">
            <span class="theme-swatch" :style="{ background: `linear-gradient(135deg, ${t.swatch[0]} 50%, ${t.swatch[1]} 50%)` }" />
            <span>{{ t.name }}</span>
          </button>
        </div>
      </div>

      <!-- User section -->
      <div class="p-2 sidebar-user-section shrink-0">
        <div v-if="currentUser" class="flex items-center gap-2">
          <div class="relative w-6 h-6 shrink-0">
            <div class="w-6 h-6 rounded-full bg-violet-700 flex items-center justify-center">
              <i class="pi pi-user text-[10px] text-violet-200" />
            </div>
            <!-- Online indicator -->
            <span class="sidebar-online-dot"></span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium truncate text-violet-100">{{ currentUser.username }}</div>
            <div class="text-[10px] sidebar-online-text flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full sidebar-online-dot inline-block"></span> 在线
            </div>
          </div>
        </div>
        <div v-else class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-full bg-zinc-600 flex items-center justify-center shrink-0">
            <i class="pi pi-user text-[10px] text-zinc-400" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium truncate text-zinc-500">未登录</div>
            <div class="text-[10px] text-zinc-600 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-zinc-500 inline-block"></span> 离线
            </div>
          </div>
        </div>
        <button @click="handleLogout" class="mt-1.5 w-full text-left text-[10px] sidebar-logout-text flex items-center gap-1.5 transition-colors">
          <i class="pi pi-sign-out text-[10px]" /> 退出登录
        </button>
      </div>
    </aside>

    <!-- Main content with subtle background -->
    <div class="flex-1 flex flex-col overflow-hidden main-content-bg">
      <!-- Top bar -->
      <header class="h-10 bg-white/80 backdrop-blur-sm border-b border-zinc-200/50 flex items-center justify-between px-6 shrink-0 no-print">
        <h1 class="text-sm font-light text-zinc-700 tracking-tight">
          {{ menuItems.find(i => i.to === route.path)?.label || (route.path === '/init' ? '初始化导航' : '首页') }}
        </h1>
        <div class="flex items-center gap-4">
          <a href="https://www.onemipham.com" target="_blank" class="text-xs text-zinc-400 hover:text-zinc-600 transition-colors">
            公司网站
          </a>
          <button class="p-1.5 rounded hover:bg-zinc-100/50 relative">
            <i class="pi pi-bell text-zinc-400 text-xs" />
          </button>
        </div>
      </header>

      <!-- Toast notification -->
      <div
        v-if="notificationMessage"
        class="fixed top-4 right-4 z-50 bg-red-700 text-white text-xs px-4 py-2.5 rounded-sm shadow-lg transition-all max-w-xs"
      >
        <div class="flex items-center gap-2">
          <i class="pi pi-lock text-xs" />
          <span>{{ notificationMessage }}</span>
        </div>
      </div>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-4">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.marquee-text {
  animation: marquee 18s linear infinite;
  display: inline-block;
  padding-left: 100%;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
</style>
