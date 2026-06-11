<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import { listPeriods, closePeriod, unclosePeriod, getCloseChecks } from '@/api'
import Textarea from 'primevue/textarea'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const year = ref(new Date().getFullYear())
const periods = ref<any[]>([])
const loading = ref(false)
const showChecks = ref(false)
const checks = ref<any>(null)
const checkPeriod = ref('')
const showUnclose = ref(false)
const uncloseReason = ref('')
const uncloseTarget = ref('')

const months = Array.from({ length: 12 }, (_, i) => {
  const m = String(i + 1).padStart(2, '0')
  return `${year.value}-${m}`
})

function getStatus(period: string) {
  const p = periods.value.find((x: any) => x.period === period)
  return p?.is_closed ? 'closed' : 'open'
}

async function load() {
  loading.value = true
  try {
    const res = await listPeriods(companyId.value)
    periods.value = res.data
  } finally { loading.value = false }
}

async function runChecks(period: string) {
  checkPeriod.value = period
  try {
    const res = await getCloseChecks(companyId.value, period)
    checks.value = res.data
    showChecks.value = true
  } catch (e: any) { alert(e.response?.data?.detail) }
}

async function doClose(period: string) {
  try {
    await closePeriod(companyId.value, period)
    showChecks.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail) }
}

function openUnclose(period: string) {
  uncloseTarget.value = period
  uncloseReason.value = ''
  showUnclose.value = true
}

async function doUnclose() {
  try {
    await unclosePeriod(companyId.value, uncloseTarget.value, uncloseReason.value)
    showUnclose.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail) }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">月度结账</h2>
      <div class="flex gap-2 items-center">
        <Button icon="pi pi-chevron-left" text rounded @click="year--; load()" />
        <span class="text-xl font-bold text-zinc-700 w-20 text-center">{{ year }}</span>
        <Button icon="pi pi-chevron-right" text rounded @click="year++; load()" />
      </div>
    </div>

    <div class="grid grid-cols-4 gap-3">
      <div v-for="m in months" :key="m"
        class="bg-white rounded-sm border p-4 flex flex-col gap-2"
        :class="getStatus(m) === 'closed' ? 'border-green-300' : 'border-stone-200'">
        <div class="flex justify-between items-center">
          <span class="font-bold text-zinc-700">{{ m }}</span>
          <Tag :value="getStatus(m) === 'closed' ? '已关账' : '未关账'"
            :severity="getStatus(m) === 'closed' ? 'success' : 'warning'" />
        </div>
        <div class="flex gap-1 mt-2">
          <Button v-if="getStatus(m) === 'open'" label="检查" text size="small" severity="info"
            @click="runChecks(m)" class="flex-1" />
          <Button v-if="getStatus(m) === 'closed'" label="反结账" text size="small" severity="danger"
            @click="openUnclose(m)" class="flex-1" />
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showChecks" :header="`结账检查 - ${checkPeriod}`" :style="{ width: '500px' }" :modal="true">
      <div v-if="checks" class="flex flex-col gap-4 py-4">
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-stone-50 rounded p-3 text-center">
            <div class="text-sm text-zinc-500">未过账凭证</div>
            <div class="text-2xl font-bold" :class="checks.unposted_vouchers > 0 ? 'text-red-600' : 'text-green-600'">
              {{ checks.unposted_vouchers }}
            </div>
          </div>
          <div class="bg-stone-50 rounded p-3 text-center">
            <div class="text-sm text-zinc-500">试算不平衡</div>
            <div class="text-2xl font-bold" :class="checks.unbalanced_vouchers > 0 ? 'text-red-600' : 'text-green-600'">
              {{ checks.unbalanced_vouchers }}
            </div>
          </div>
        </div>
        <p class="text-sm" :class="checks.can_close ? 'text-green-600' : 'text-red-600'">{{ checks.message }}</p>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showChecks = false" />
        <Button label="执行关账" icon="pi pi-lock" severity="success" @click="doClose(checkPeriod)" :disabled="!checks || !checks.can_close" />
      </template>
    </Dialog>

    <Dialog v-model:visible="showUnclose" header="反结账" :style="{ width: '450px' }" :modal="true">
      <div class="flex flex-col gap-4 py-4">
        <p class="text-sm text-zinc-600">期间：{{ uncloseTarget }}</p>
        <label class="block text-xs text-zinc-500 mb-1">原因（必填）</label>
        <Textarea v-model="uncloseReason" rows="3" class="w-full" />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showUnclose = false" />
        <Button label="确认反结账" icon="pi pi-exclamation-triangle" severity="danger" @click="doUnclose" :disabled="!uncloseReason" />
      </template>
    </Dialog>
  </div>
</template>
