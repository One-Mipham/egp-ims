<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { login } from '@/api'
import { getCurrentSubscription } from '@/api/subscriptions'
import { useI18n } from '@/i18n'
import LangToggle from '@/components/LangToggle.vue'

const { t, locale } = useI18n()

const router = useRouter()
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const companyId = ref('')
const companyName = ref('')
const companyShortName = ref('')
const identified = ref(false)
const selectedPeriod = ref('')
const systemDate = ref('')
const accountingDate = ref('')
const isAdmin = ref(false)
const error = ref('')
const loading = ref(false)
const identifying = ref(false)

// 模板引用 — 用于自动填充安全网（绕过 v-model 的 input 事件依赖）
const usernameInput = ref<HTMLInputElement | null>(null)
const passwordInput = ref<HTMLInputElement | null>(null)

/**
 * 从 DOM 读取真实值，防止浏览器自动填充绕过 Vue 响应式系统。
 * v-model 依赖 input 事件，但浏览器自动填充经常不触发该事件，
 * 导致 username.value / password.value 为空而 DOM 显示有值。
 */
function syncFromDOM() {
  if (usernameInput.value) username.value = usernameInput.value.value
  if (passwordInput.value) password.value = passwordInput.value.value
}

function defaultDateStr(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function defaultPeriodStr(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

onMounted(() => {
  localStorage.removeItem('token')
  localStorage.removeItem('companyId')
  const now = new Date()
  systemDate.value = defaultDateStr(now)
  accountingDate.value = defaultDateStr(now)
  selectedPeriod.value = defaultPeriodStr(now)
})

async function handleIdentify() {
  syncFromDOM() // 安全网：浏览器自动填充
  if (!username.value) {
    error.value = t('login.usernameRequired') || '请输入用户名'
    return
  }
  if (!password.value) {
    error.value = t('login.passwordRequired') || '请输入密码'
    return
  }
  identifying.value = true
  error.value = ''
  identified.value = false
  try {
    const res = await api.post('/auth/identify', {
      username: username.value,
      password: password.value,
    })
    companyId.value = String(res.data.company_id)
    companyName.value = res.data.company_name
    companyShortName.value = res.data.company_short_name
    identified.value = true
  } catch (e: any) {
    if (e.response) {
      error.value = e.response.data?.detail || t('login.loginFailed')
    } else if (e.request) {
      error.value = t('login.networkError') || '网络连接失败，请检查网络后重试'
    } else {
      error.value = t('login.loginFailed')
    }
    console.error('[Login] 识别失败:', e)
    password.value = ''
  } finally {
    identifying.value = false
  }
}

async function handleLogin() {
  syncFromDOM() // 安全网：浏览器自动填充
  if (!username.value) {
    error.value = t('login.usernameRequired') || '请输入用户名'
    return
  }
  if (!password.value) {
    error.value = t('login.passwordRequired') || '请输入密码'
    return
  }
  if (!companyId.value) {
    error.value = t('login.companyNotIdentified') || '请先完成公司识别'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await login({
      username: username.value,
      password: password.value,
      company_id: Number(companyId.value),
      period: selectedPeriod.value,
      is_admin: isAdmin.value,
    })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('companyId', String(res.data.company_id))
    localStorage.setItem('companyName', res.data.company_name)
    localStorage.setItem('username', res.data.username)
    localStorage.setItem('role', res.data.role)
    localStorage.setItem('systemDate', systemDate.value)
    localStorage.setItem('accountingDate', accountingDate.value)
    try {
      const subRes = await getCurrentSubscription(res.data.company_id)
      localStorage.setItem('enabledModules', JSON.stringify(subRes.data.enabled_modules || []))
      localStorage.setItem('subscriptionStatus', subRes.data.subscription_status || 'trialing')
      localStorage.setItem('moduleSet', subRes.data.module_set || 'trial')
    } catch (_) {
      localStorage.setItem('subscriptionStatus', 'trialing')
      localStorage.setItem('enabledModules', '[]')
    }
    // fresh=1 告知路由守卫这是刚登录的 token，放行至首页
    router.push('/?fresh=1')
  } catch (e: any) {
    if (e.response) {
      error.value = e.response.data?.detail || t('login.loginFailed')
    } else if (e.request) {
      error.value = t('login.networkError') || '网络连接失败，请检查网络后重试'
    } else {
      error.value = t('login.loginFailed')
    }
    console.error('[Login] 登录失败:', e)
    password.value = ''
    identified.value = false
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-bg min-h-screen flex flex-col">
    <!-- Top bar -->
    <header class="h-16 bg-black/50 backdrop-blur-sm flex items-center justify-between px-10 shrink-0 z-10">
      <div class="flex items-center gap-3">
        <img src="/company-logo.jpg" alt="MiphamAI" class="h-10 w-auto rounded-sm" />
        <span v-if="locale !== 'en-US'" class="text-lg font-medium text-white/80 tracking-wider">{{
          t('app.company')
        }}</span>
      </div>
      <div v-if="locale !== 'en-US'" class="flex items-center gap-4">
        <LangToggle />
      </div>
    </header>

    <!-- Login area -->
    <div class="flex-1 flex items-center justify-center px-4">
      <div class="w-full max-w-lg">
        <!-- Title -->
        <div class="mb-10">
          <h1 class="text-4xl font-light text-white tracking-tight">
            {{ t('login.title') }}
          </h1>
          <p class="text-lg text-white/40 mt-2 tracking-wide font-light">
            {{ t('login.subtitle') }}
          </p>
          <div class="mt-4 w-10 h-px bg-indigo-500" />
        </div>

        <!-- Error -->
        <div
          v-if="error"
          class="mb-5 p-3 bg-red-900/80 border border-red-700/50 rounded-sm text-sm text-red-100 tracking-wide"
        >
          {{ error }}
        </div>

        <!-- Login form card -->
        <div class="bg-white/10 backdrop-blur-md border border-white/20 rounded-sm p-8">
          <!-- 用户名 -->
          <label class="block text-base font-medium text-white/70 mb-2 tracking-wider uppercase">{{
            t('login.username')
          }}</label>
          <input
            ref="usernameInput"
            v-model="username"
            type="text"
            class="w-full px-4 py-3 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 focus:border-white/50 outline-none text-base tracking-wide transition-colors"
            :placeholder="t('login.usernamePlaceholder')"
            autocomplete="username"
            @keyup.enter="identified ? handleLogin() : handleIdentify()"
            @change="username = ($event.target as HTMLInputElement).value"
          />

          <!-- 密码（带眼睛） -->
          <label class="block text-base font-medium text-white/70 mb-2 mt-4 tracking-wider uppercase">{{
            t('login.password')
          }}</label>
          <div class="relative">
            <input
              ref="passwordInput"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="w-full px-4 py-3 pr-12 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 focus:border-white/50 outline-none text-base tracking-wide transition-colors"
              :placeholder="t('login.passwordPlaceholder')"
              autocomplete="current-password"
              @keyup.enter="identified ? handleLogin() : handleIdentify()"
              @change="password = ($event.target as HTMLInputElement).value"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition-colors p-1"
              :title="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <!-- 眼睛图标（SVG） -->
              <svg
                v-if="!showPassword"
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                />
              </svg>
            </button>
          </div>

          <!-- Step 1: Identify company -->
          <div v-if="!identified" class="mt-6 space-y-3">
            <button
              @click="handleIdentify"
              :disabled="!username || !password || identifying"
              class="w-full py-3 bg-indigo-700 text-white text-sm font-medium rounded-sm hover:bg-indigo-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all tracking-wider uppercase"
            >
              {{ identifying ? '...' : t('login.signIn') }}
            </button>
            <div class="text-center">
              <router-link
                to="/register"
                class="text-sm text-white/50 hover:text-white/70 transition-colors tracking-wide"
              >
                {{ t('login.registerNew') }}
              </router-link>
            </div>
          </div>

          <!-- Step 2: Company confirmed → login -->
          <div v-if="identified" class="mt-4 space-y-3">
            <div class="bg-black/30 rounded-sm p-4 border border-white/10">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-white/50">{{ t('login.companyId') }}</span>
                <span class="text-white font-mono font-bold">{{ companyId }}</span>
              </div>
              <div class="flex justify-between text-sm mb-1">
                <span class="text-white/50">{{ locale === 'en-US' ? 'Company' : '公司全称' }}</span>
                <span class="text-white text-right">{{ companyName }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-white/50">{{ locale === 'en-US' ? 'Short Name' : '公司简称' }}</span>
                <span class="text-white text-right">{{ companyShortName }}</span>
              </div>
            </div>

            <!-- Period & date row -->
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="block text-xs text-white/50 mb-1">{{ t('login.period') }}</label>
                <input
                  v-model="selectedPeriod"
                  type="month"
                  class="w-full px-3 py-2 border border-white/20 rounded-sm bg-white/10 text-white text-sm focus:ring-1 focus:ring-white/40 outline-none"
                />
              </div>
              <div class="flex-1">
                <label class="block text-xs text-white/50 mb-1">{{ t('login.systemDate') }}</label>
                <input
                  v-model="systemDate"
                  type="date"
                  class="w-full px-3 py-2 border border-white/20 rounded-sm bg-white/10 text-white text-sm focus:ring-1 focus:ring-white/40 outline-none"
                />
              </div>
            </div>

            <div class="flex items-center justify-between">
              <router-link
                to="/register"
                class="text-sm text-white/50 hover:text-white/70 transition-colors tracking-wide"
              >
                {{ t('login.registerNew') }}
              </router-link>
              <div class="flex gap-2 items-center">
                <label class="flex items-center gap-1 text-xs text-white/40 cursor-pointer">
                  <input v-model="isAdmin" type="checkbox" class="rounded-sm border-white/30" />
                  {{ t('login.adminMode') }}
                </label>
                <button
                  @click="handleLogin"
                  :disabled="loading"
                  class="px-8 py-2.5 bg-indigo-700 text-white text-sm font-medium rounded-sm hover:bg-indigo-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all tracking-wider uppercase"
                >
                  {{ loading ? '...' : t('login.signIn') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-8 pt-4 border-t border-white/10 text-center">
          <p class="text-xs text-white/30 tracking-wide">{{ t('login.developer') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-bg {
  background:
    linear-gradient(rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.45)),
    url('/login-bg.jpg') center/cover no-repeat fixed;
}
</style>
