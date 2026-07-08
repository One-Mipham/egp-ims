<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import { useI18n } from '@/i18n'

const { t, locale } = useI18n()
const router = useRouter()
const paymentMethod = ref('bank_transfer')
const selectedPlan = ref<any>(null)
const receiptFile = ref<any>(null)

const paymentMethods = computed(() => {
  if (locale.value === 'en-US') {
    return [
      {
        value: 'bank_transfer',
        label: t('subscription.checkout.bankTransfer'),
        icon: 'pi pi-building',
        desc: t('subscription.checkout.bankDesc'),
      },
      {
        value: 'paypal',
        label: t('subscription.checkout.paypal'),
        icon: 'pi pi-paypal',
        desc: t('subscription.checkout.paypalDesc'),
      },
      {
        value: 'stripe',
        label: t('subscription.checkout.stripe'),
        icon: 'pi pi-credit-card',
        desc: t('subscription.checkout.stripeDesc'),
      },
    ]
  }
  return [
    {
      value: 'bank_transfer',
      label: t('subscription.checkout.bankTransfer'),
      icon: 'pi pi-building',
      desc: t('subscription.checkout.bankDesc'),
    },
    {
      value: 'alipay',
      label: t('subscription.checkout.alipay'),
      icon: 'pi pi-mobile',
      desc: t('subscription.checkout.alipayDesc'),
    },
    {
      value: 'wechat',
      label: t('subscription.checkout.wechat'),
      icon: 'pi pi-comments',
      desc: t('subscription.checkout.wechatDesc'),
    },
  ]
})

const showBankInfo = computed(() => paymentMethod.value === 'bank_transfer')
const showQRCode = computed(() => paymentMethod.value === 'alipay' || paymentMethod.value === 'wechat')
const isTrialVerification = computed(() => selectedPlan.value?.is_trial_verification === true)

const displayPrice = computed(() => {
  if (!selectedPlan.value) return ''
  if (locale.value === 'en-US') {
    return (
      '$' +
      (selectedPlan.value.price / 7.2).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    )
  }
  return '¥' + selectedPlan.value.price?.toLocaleString('zh-CN')
})

const billingCycleLabel = computed(() => {
  if (!selectedPlan.value) return ''
  const bc = selectedPlan.value.billing_cycle
  if (bc === 'monthly') return locale.value === 'en-US' ? 'Monthly' : '月付'
  if (bc === 'annual') return locale.value === 'en-US' ? 'Annual' : '年付'
  return locale.value === 'en-US' ? 'One-Time' : '一次性'
})

const currency = computed(() => (locale.value === 'en-US' ? 'USD' : 'CNY'))

onMounted(() => {
  const stored = localStorage.getItem('selectedPlan')
  if (stored) {
    selectedPlan.value = JSON.parse(stored)
  } else {
    router.push('/subscription/plans')
  }
})

function onFileSelect(event: any) {
  receiptFile.value = event.files?.[0] || null
}

function confirmPayment() {
  if (!selectedPlan.value) return
  const pm = paymentMethods.value.find(p => p.value === paymentMethod.value)
  const amt =
    locale.value === 'en-US'
      ? '$' + Math.round(selectedPlan.value.price / 7.2).toLocaleString('en-US')
      : '¥' + selectedPlan.value.price?.toLocaleString('zh-CN')
  const receiptMsg = receiptFile.value
    ? locale.value === 'en-US'
      ? `\nReceipt: ${receiptFile.value.name}`
      : `\n转账回单: ${receiptFile.value.name}`
    : ''
  alert(
    `${locale.value === 'en-US' ? 'Payment simulated' : '模拟支付成功'}：${selectedPlan.value.name} - ${amt} (${pm?.label})${receiptMsg}\n${locale.value === 'en-US' ? 'Payment integration will be implemented in Phase 3.' : '支付功能将在 Phase 3 实现。'}`,
  )
  localStorage.removeItem('selectedPlan')
  if (isTrialVerification.value) {
    router.push('/?fresh=1')
  } else {
    router.push('')
  }
}
</script>

<template>
  <div class="min-h-screen bg-stone-50 py-12 px-4">
    <div class="max-w-lg mx-auto">
      <h1 class="text-2xl font-bold text-stone-800 mb-2">{{ t('subscription.checkout.title') }}</h1>
      <p class="text-sm text-stone-500 mb-8">{{ t('subscription.checkout.subtitle') }}</p>

      <!-- Selected plan summary -->
      <div v-if="selectedPlan" class="bg-white rounded-xl border border-stone-200 p-6 mb-6">
        <h3 class="font-bold text-stone-800">{{ selectedPlan.name }}</h3>
        <div class="text-2xl font-bold text-stone-800 mt-2">{{ displayPrice }}</div>
        <p class="text-xs text-stone-400 mt-1">{{ billingCycleLabel }} · {{ currency }}</p>
      </div>

      <!-- Payment method selection -->
      <div class="bg-white rounded-xl border border-stone-200 p-6 mb-6">
        <h4 class="font-medium text-stone-700 mb-4">{{ locale === 'en-US' ? 'Payment Method' : '支付方式' }}</h4>
        <div
          v-for="pm in paymentMethods"
          :key="pm.value"
          class="flex items-center gap-4 p-3 rounded-lg cursor-pointer hover:bg-stone-50 transition-colors mb-2"
          :class="{ 'bg-indigo-50 border border-indigo-200': paymentMethod === pm.value }"
          @click="paymentMethod = pm.value"
        >
          <RadioButton v-model="paymentMethod" :value="pm.value" />
          <div class="flex-1">
            <div class="text-sm font-medium text-stone-700">{{ pm.label }}</div>
            <div class="text-xs text-stone-400">{{ pm.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 收款码（支付宝/微信） -->
      <div v-if="showQRCode" class="bg-white rounded-xl border border-stone-200 p-6 mb-6 text-center">
        <h4 class="font-medium text-stone-700 mb-3">
          {{ locale === 'en-US' ? 'Scan to Pay' : '扫码支付' }}
        </h4>
        <img src="/payment-qr.jpg" alt="收款码" class="w-48 h-48 mx-auto rounded-lg border border-stone-200" />
        <p class="text-xs text-stone-400 mt-3">
          {{
            locale === 'en-US'
              ? 'Scan the QR code with Alipay or WeChat. Include your Company ID in the payment note.'
              : '请使用支付宝或微信扫描二维码支付，付款时请备注公司编号。'
          }}
        </p>
      </div>

      <!-- Bank account info (visible when bank transfer selected) -->
      <div v-if="showBankInfo" class="bg-stone-50 rounded-xl border border-stone-200 p-6 mb-6">
        <h4 class="font-medium text-stone-700 mb-3">
          {{ locale === 'en-US' ? 'Bank Account Details' : '收款账户信息' }}
        </h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-stone-500">{{ locale === 'en-US' ? 'Account Name' : '户名' }}</span>
            <span class="font-mono text-stone-700">北京华安麦逄科技有限公司</span>
          </div>
          <div class="flex justify-between">
            <span class="text-stone-500">{{ locale === 'en-US' ? 'Bank' : '开户行' }}</span>
            <span class="font-mono text-stone-700">{{
              locale === 'en-US' ? 'ICBC Beijing Haidian Branch' : '中国工商银行北京海淀支行'
            }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-stone-500">{{ locale === 'en-US' ? 'Account Number' : '账号' }}</span>
            <span class="font-mono text-stone-700">0200 0045 0920 0123 456</span>
          </div>
        </div>
        <p class="text-xs text-stone-400 mt-3 leading-relaxed">
          {{
            locale === 'en-US'
              ? 'Please include your Company ID in the transfer reference. We will activate your subscription within 1 business day of receiving payment.'
              : '转账时请在附言中注明公司编号。收到款项后1个工作日内开通订阅。'
          }}
        </p>
      </div>

      <!-- Upload transfer receipt (bank transfer only) -->
      <div v-if="showBankInfo" class="bg-white rounded-xl border border-stone-200 p-6 mb-6">
        <h4 class="font-medium text-stone-700 mb-3">
          {{ locale === 'en-US' ? 'Upload Transfer Receipt' : '上传转账回单' }}
        </h4>
        <p class="text-xs text-stone-400 mb-3">
          {{
            locale === 'en-US'
              ? 'Upload a screenshot or photo of your bank transfer to expedite verification.'
              : '上传银行转账回单截图或照片，可加速审核开通。'
          }}
        </p>
        <div
          class="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors cursor-pointer"
          @click="($refs.fileInput as any)?.click()"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*,.pdf"
            class="hidden"
            @change="(e: any) => onFileSelect({ files: e.target.files })"
          />
          <template v-if="!receiptFile">
            <i class="pi pi-cloud-upload text-2xl text-stone-400 mb-2 block" />
            <p class="text-sm text-stone-500">{{ locale === 'en-US' ? 'Click to upload' : '点击上传' }}</p>
            <p class="text-xs text-stone-400 mt-1">
              {{ locale === 'en-US' ? 'PNG, JPG or PDF, max 5MB' : '支持 PNG、JPG、PDF，最大 5MB' }}
            </p>
          </template>
          <template v-else>
            <i class="pi pi-check-circle text-2xl text-emerald-500 mb-2 block" />
            <p class="text-sm font-medium text-emerald-700">{{ receiptFile.name }}</p>
            <p class="text-xs text-stone-400 mt-1 cursor-pointer hover:text-red-500" @click.stop="receiptFile = null">
              {{ locale === 'en-US' ? 'Remove' : '移除' }}
            </p>
          </template>
        </div>
      </div>

      <Button
        :label="t('subscription.checkout.confirmPay')"
        icon="pi pi-check"
        class="w-full"
        size="large"
        @click="confirmPayment"
      />
      <Button
        :label="t('subscription.checkout.backToPlans')"
        severity="secondary"
        text
        class="w-full mt-2"
        @click="router.push('/subscription/plans')"
      />
    </div>
  </div>
</template>
