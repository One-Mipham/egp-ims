<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import { listPlans, activateTrial, type SubscriptionPlan } from '@/api/subscriptions'
import { useI18n } from '@/i18n'

const { t } = useI18n()
const router = useRouter()
const plans = ref<SubscriptionPlan[]>([])
const selectedCycle = ref<'monthly' | 'annual'>('annual')
const loading = ref(false)

function isSubscriptionCycle(plan: SubscriptionPlan): boolean {
  return plan.billing_cycle === 'monthly' || plan.billing_cycle === 'semi_annual' || plan.billing_cycle === 'annual'
}

function isLifetime(plan: SubscriptionPlan): boolean {
  return plan.billing_cycle === 'lifetime'
}

const displayPlans = computed(() => {
  // Group: show monthly OR annual plans, plus lifetime
  const cyclePlans = plans.value.filter(
    p =>
      (selectedCycle.value === 'monthly' && p.billing_cycle === 'monthly') ||
      (selectedCycle.value === 'annual' && p.billing_cycle === 'annual'),
  )
  const lifetime = plans.value.filter(p => p.billing_cycle === 'lifetime')
  return { cyclePlans, lifetime }
})

function getModuleLabel(m: string) {
  return t(`modules.${m}`) || m
}

function formatPrice(price: number) {
  if (price === 0) return t('subscription.free')
  return '¥' + price.toLocaleString('zh-CN')
}

function selectPlan(plan: SubscriptionPlan) {
  const companyId = localStorage.getItem('companyId') || '1'
  // For now: store selection and redirect. Checkout will be Phase 3.
  localStorage.setItem(
    'selectedPlan',
    JSON.stringify({ slug: plan.slug, name: plan.name, price: plan.price_cny, billing_cycle: plan.billing_cycle }),
  )
  router.push('/subscription/checkout')
}

async function startTrial() {
  loading.value = true
  try {
    const companyId = parseInt(localStorage.getItem('companyId') || '0')
    await activateTrial(companyId)
    router.push('')
  } catch (e: any) {
    alert(e.response?.data?.detail || t('subscription.activateFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await listPlans()
    plans.value = res.data
  } catch (e) {
    console.error('Failed to load plans', e)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-stone-50 to-white py-12 px-4">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-stone-800 mb-3">{{ t('subscription.title') }}</h1>
        <p class="text-stone-500 max-w-2xl mx-auto">
          {{ t('subscription.subtitle') }}
        </p>

        <!-- Cycle toggle -->
        <div class="inline-flex items-center bg-stone-100 rounded-lg p-1 mt-6">
          <button
            @click="selectedCycle = 'monthly'"
            class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
            :class="selectedCycle === 'monthly' ? 'bg-white text-stone-800 shadow-sm' : 'text-stone-500'"
          >
            {{ t('subscription.monthly') }}
          </button>
          <button
            @click="selectedCycle = 'annual'"
            class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
            :class="selectedCycle === 'annual' ? 'bg-white text-stone-800 shadow-sm' : 'text-stone-500'"
          >
            {{ t('subscription.annual') }}
            <span class="text-xs text-emerald-600 ml-1">{{ t('subscription.savePercent') }}</span>
          </button>
        </div>
      </div>

      <!-- Plan cards -->
      <div class="grid md:grid-cols-3 gap-6 mb-12">
        <div
          v-for="plan in displayPlans.cyclePlans"
          :key="plan.slug"
          class="bg-white rounded-xl border border-stone-200 p-6 hover:shadow-lg transition-shadow flex flex-col"
          :class="{ 'border-indigo-400 ring-2 ring-indigo-100': plan.slug === 'pro' || plan.slug === 'pro-annual' }"
        >
          <div class="flex-1">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-bold text-stone-800">{{ plan.name }}</h3>
              <Badge
                v-if="plan.slug === 'pro' || plan.slug === 'pro-annual'"
                :value="t('subscription.recommended')"
                severity="info"
              />
            </div>
            <p class="text-xs text-stone-500 mb-4">{{ plan.description }}</p>

            <div class="mb-6">
              <span class="text-3xl font-bold text-stone-800">{{ formatPrice(plan.price_cny) }}</span>
              <span class="text-sm text-stone-400 ml-1">{{
                selectedCycle === 'monthly' ? t('subscription.perMonth') : t('subscription.perYear')
              }}</span>
            </div>

            <ul class="space-y-2 mb-6">
              <li v-for="m in plan.modules" :key="m" class="flex items-center gap-2 text-sm text-stone-600">
                <i class="pi pi-check-circle text-emerald-500 text-xs" />
                {{ getModuleLabel(m) }}
              </li>
            </ul>
          </div>

          <Button
            :label="plan.slug.includes('pro') ? t('subscription.subscribeNow') : t('subscription.selectPlan')"
            icon="pi pi-arrow-right"
            iconPos="right"
            class="w-full"
            :severity="plan.slug.includes('pro') ? undefined : 'secondary'"
            @click="selectPlan(plan)"
          />
        </div>
      </div>

      <!-- Buyout section -->
      <div v-if="displayPlans.lifetime.length" class="max-w-3xl mx-auto">
        <h3 class="text-lg font-bold text-stone-800 mb-4 text-center">{{ t('subscription.buyout') }}</h3>
        <div
          v-for="plan in displayPlans.lifetime"
          :key="plan.slug"
          class="bg-stone-50 rounded-xl border border-stone-200 p-6 mb-4 flex items-center justify-between"
        >
          <div>
            <h4 class="font-bold text-stone-800">{{ plan.name }}</h4>
            <p class="text-xs text-stone-500 mt-1">{{ plan.description }}</p>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold text-stone-800">{{ formatPrice(plan.price_cny) }}</div>
            <Button
              :label="t('subscription.inquire')"
              severity="secondary"
              size="small"
              class="mt-2"
              @click="selectPlan(plan)"
            />
          </div>
        </div>
      </div>

      <!-- Start trial CTA -->
      <div class="text-center mt-8">
        <Button
          :label="t('subscription.startTrial')"
          icon="pi pi-play"
          size="large"
          rounded
          :loading="loading"
          @click="startTrial"
        />
      </div>
    </div>
  </div>
</template>
