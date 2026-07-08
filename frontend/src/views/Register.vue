<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api'
import { activateTrial } from '@/api/subscriptions'
import { useI18n } from '@/i18n'
import LangToggle from '@/components/LangToggle.vue'

const { t, locale } = useI18n()

const router = useRouter()

const phone = ref('')
const companyName = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)
const redirecting = ref(false)

const phoneError = ref('')
const pwdError = ref('')

function validatePhone() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    phoneError.value = t('register.phoneError')
  } else {
    phoneError.value = ''
  }
}

function validatePassword() {
  if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(password.value)) {
    pwdError.value = t('register.passwordError')
  } else {
    pwdError.value = ''
  }
}

async function handleRegister() {
  error.value = ''
  if (!phone.value || !companyName.value || !password.value) {
    error.value = t('register.fillAll')
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = t('register.passwordMismatch')
    return
  }
  if (pwdError.value || phoneError.value) return

  loading.value = true
  try {
    const res = await register({
      phone: phone.value,
      company_name: companyName.value,
      password: password.value,
    })
    result.value = res.data
    // 自动激活30天试用
    redirecting.value = true
    try {
      await activateTrial(res.data.company_id)
    } catch (_e) {
      /* ok */
    }
    // 存储 ¥0.99 验证支付信息，跳转结算页
    localStorage.setItem(
      'selectedPlan',
      JSON.stringify({
        name: '实名验证',
        slug: 'id-verification',
        price: 0.99,
        billing_cycle: 'once',
        is_trial_verification: true,
      }),
    )
    setTimeout(() => {
      router.push('/subscription/checkout')
    }, 2500)
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('register.registerFailed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="mb-8 text-center">
        <div class="flex items-center justify-center gap-3 mb-3">
          <img src="/company-logo.jpg" alt="MiphamAI" class="h-10 w-auto rounded-sm" />
          <span v-if="locale !== 'en-US'" class="text-white/40 text-sm tracking-widest">{{ t('app.company') }}</span>
        </div>
        <div class="flex items-center justify-center gap-4">
          <h1 class="text-2xl font-light text-white tracking-wide">{{ t('register.title') }}</h1>
          <LangToggle v-if="locale !== 'en-US'" />
        </div>
        <p class="text-sm text-white/40 mt-1">{{ t('register.subtitle') }}</p>
      </div>

      <!-- Error -->
      <div v-if="error" class="mb-5 p-3 bg-red-900/80 border border-red-700/50 rounded-sm text-sm text-red-100">
        {{ error }}
      </div>

      <!-- Success / redirecting -->
      <div v-if="result" class="bg-white/10 backdrop-blur-md border border-white/20 rounded-sm p-6">
        <div class="text-center mb-4">
          <div class="w-14 h-14 rounded-full bg-emerald-600/30 flex items-center justify-center mx-auto mb-3">
            <i class="pi pi-check text-2xl text-emerald-300" />
          </div>
          <h2 class="text-lg font-medium text-white">{{ t('register.success') }}</h2>
          <p class="text-sm text-white/50 mt-2">{{ redirecting ? t('register.redirecting') : '...' }}</p>
        </div>

        <div class="space-y-2 bg-black/20 rounded-sm p-4 font-mono text-sm">
          <div class="flex justify-between">
            <span class="text-white/50">{{ t('register.companyIdLabel') }}</span>
            <span class="text-white font-bold">{{ result.company_id }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-white/50">{{ t('register.companyNameLabel') }}</span>
            <span class="text-white">{{ result.company_name }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-white/50">{{ t('register.phoneLabel') }}</span>
            <span class="text-white">{{ result.phone }}</span>
          </div>
        </div>

        <p class="text-xs text-amber-300/70 mt-4 text-center">
          {{ t('register.screenshot') }}
        </p>

        <button
          @click="router.push('/subscription/checkout')"
          class="w-full mt-3 px-6 py-2.5 bg-indigo-700 text-white text-sm font-medium rounded-sm hover:bg-indigo-800 transition-all"
        >
          ¥0.99 实名验证
        </button>
      </div>

      <!-- Registration form -->
      <div v-else class="bg-white/10 backdrop-blur-md border border-white/20 rounded-sm p-6">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-white/70 mb-1.5 tracking-wide">{{
              t('register.phone')
            }}</label>
            <input
              v-model="phone"
              type="tel"
              class="w-full px-3 py-2.5 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 outline-none text-sm"
              :placeholder="t('register.phonePlaceholder')"
              maxlength="11"
              @blur="validatePhone"
              @input="phoneError = ''"
            />
            <p v-if="phoneError" class="text-xs text-red-400 mt-1">{{ phoneError }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-white/70 mb-1.5 tracking-wide">{{
              t('register.companyName')
            }}</label>
            <input
              v-model="companyName"
              type="text"
              class="w-full px-3 py-2.5 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 outline-none text-sm"
              :placeholder="t('register.companyNamePlaceholder')"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-white/70 mb-1.5 tracking-wide">{{
              t('register.password')
            }}</label>
            <input
              v-model="password"
              type="password"
              class="w-full px-3 py-2.5 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 outline-none text-sm"
              :placeholder="t('register.passwordPlaceholder')"
              @blur="validatePassword"
              @input="pwdError = ''"
            />
            <p v-if="pwdError" class="text-xs text-red-400 mt-1">{{ pwdError }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-white/70 mb-1.5 tracking-wide">{{
              t('register.confirmPassword')
            }}</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="w-full px-3 py-2.5 border border-white/20 rounded-sm bg-white/10 text-white placeholder-white/30 focus:ring-1 focus:ring-white/40 outline-none text-sm"
              :placeholder="t('register.confirmPasswordPlaceholder')"
              @keyup.enter="handleRegister"
            />
          </div>

          <button
            @click="handleRegister"
            :disabled="loading || !phone || !companyName || !password || !confirmPassword"
            class="w-full py-2.5 bg-indigo-700 text-white text-sm font-medium rounded-sm hover:bg-indigo-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all tracking-wider"
          >
            {{ loading ? t('register.registering') : t('register.register') }}
          </button>
        </div>

        <div class="mt-4 pt-4 border-t border-white/10 text-center">
          <router-link to="/login" class="text-sm text-white/40 hover:text-white/60 transition-colors">
            {{ t('register.hasAccount') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
