<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Card from 'primevue/card'
import api from '@/api/index'
import { listPortfolios } from '@/api'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const configs = ref<any[]>([])
const portfolios = ref<any[]>([])
const activeConfig = ref<any>(null)
const configLoading = ref(false)
const showConfigDialog = ref(false)
const isEditConfig = ref(false)
const editConfigId = ref<number | null>(null)

const configForm = ref({ name: '', portfolio_id: null as number | null, tiers: [] as any[] })

// Waterfall run
const totalProceeds = ref(0)
const result = ref<any>(null)
const runLoading = ref(false)

const TIER_TYPES = [
  { label: '返还本金 (Return of Capital)', value: 'return_of_capital' },
  { label: '门槛收益 (Preferred Return)', value: 'preferred_return' },
  { label: 'GP追补 (Catch-Up)', value: 'catch_up' },
  { label: '超额分成 (Carry Split)', value: 'carry' },
]

async function loadConfigs() {
  configLoading.value = true
  try {
    const [cRes, pRes] = await Promise.all([
      api.get('/investments/waterfall-configs', { params: { company_id: companyId.value } }),
      listPortfolios(companyId.value),
    ])
    configs.value = cRes.data
    portfolios.value = pRes.data
  } finally {
    configLoading.value = false
  }
}

function openAddConfig() {
  configForm.value = {
    name: '',
    portfolio_id: null,
    tiers: [
      { order: 1, name: '返还本金', type: 'return_of_capital', threshold_pct: 0, gp_share_pct: 0, lp_share_pct: 100 },
      { order: 2, name: '门槛收益 8%', type: 'preferred_return', threshold_pct: 8, gp_share_pct: 0, lp_share_pct: 100 },
      { order: 3, name: 'GP追补', type: 'catch_up', threshold_pct: 0, gp_share_pct: 100, lp_share_pct: 0 },
      { order: 4, name: '超额分成 20/80', type: 'carry', threshold_pct: 0, gp_share_pct: 20, lp_share_pct: 80 },
    ],
  }
  isEditConfig.value = false
  editConfigId.value = null
  showConfigDialog.value = true
}

async function saveConfig() {
  if (!configForm.value.name) return
  const data = { ...configForm.value }
  if (isEditConfig.value && editConfigId.value) {
    await api.put(`/investments/waterfall-configs/${editConfigId.value}`, data)
  } else {
    await api.post('/investments/waterfall-configs', data, { params: { company_id: companyId.value } })
  }
  showConfigDialog.value = false
  await loadConfigs()
}

async function deleteConfig(id: number) {
  if (!confirm('确定删除？')) return
  await api.delete(`/investments/waterfall-configs/${id}`)
  await loadConfigs()
}

async function runWaterfall() {
  if (!activeConfig.value || !totalProceeds.value) return
  runLoading.value = true
  try {
    const r = await api.post('/investments/waterfall/calculate', {
      config_id: activeConfig.value.id,
      total_proceeds: totalProceeds.value,
    })
    result.value = r.data
  } finally {
    runLoading.value = false
  }
}

onMounted(loadConfigs)
</script>

<template>
  <div class="p-4 space-y-6">
    <div class="flex justify-between items-center">
      <h2 class="text-lg font-semibold text-zinc-700">分配瀑布</h2>
      <Button label="新建配置" icon="pi pi-plus" size="small" @click="openAddConfig" />
    </div>

    <div class="grid grid-cols-3 gap-6">
      <!-- Config list -->
      <div class="bg-white rounded-lg border border-stone-200 p-4">
        <h3 class="font-semibold text-zinc-700 mb-3">瀑布配置</h3>
        <div v-if="configs.length === 0" class="text-sm text-stone-400">暂无配置，点击上方按钮新建</div>
        <div
          v-for="cfg in configs"
          :key="cfg.id"
          class="p-3 mb-2 rounded cursor-pointer border transition-colors"
          :class="activeConfig?.id === cfg.id ? 'border-indigo-400 bg-indigo-50' : 'border-stone-200 hover:bg-stone-50'"
          @click="activeConfig = cfg"
        >
          <div class="flex justify-between items-center">
            <span class="font-medium text-stone-700 text-sm">{{ cfg.name }}</span>
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click.stop="deleteConfig(cfg.id)" />
          </div>
          <div class="text-xs text-stone-400 mt-1">{{ cfg.tiers?.length || 0 }} 层级</div>
        </div>
      </div>

      <!-- Tiers preview -->
      <div class="col-span-2 space-y-4">
        <div v-if="activeConfig" class="bg-white rounded-lg border border-stone-200 p-4">
          <h3 class="font-semibold text-zinc-700 mb-3">{{ activeConfig.name }} — 层级结构</h3>
          <DataTable :value="activeConfig.tiers" stripedRows size="small">
            <Column field="order" header="层级" />
            <Column field="name" header="名称" />
            <Column header="类型"
              ><template #body="{ data }">{{
                data.type === 'return_of_capital'
                  ? '返还本金'
                  : data.type === 'preferred_return'
                    ? '门槛收益'
                    : data.type === 'catch_up'
                      ? '追补'
                      : '超额分成'
              }}</template></Column
            >
            <Column header="GP"
              ><template #body="{ data }">{{ data.gp_share_pct }}%</template></Column
            >
            <Column header="LP"
              ><template #body="{ data }">{{ data.lp_share_pct }}%</template></Column
            >
          </DataTable>
        </div>

        <!-- Run waterfall -->
        <div v-if="activeConfig" class="bg-white rounded-lg border border-stone-200 p-4">
          <h3 class="font-semibold text-zinc-700 mb-3">执行分配</h3>
          <div class="flex items-end gap-3">
            <div>
              <label class="text-xs text-stone-500 block mb-1">待分配总收益</label
              ><InputNumber v-model="totalProceeds" mode="currency" currency="CNY" class="w-48" />
            </div>
            <Button
              label="计算分配"
              icon="pi pi-calculator"
              @click="runWaterfall"
              :loading="runLoading"
              :disabled="!totalProceeds"
            />
          </div>
        </div>

        <!-- Results -->
        <div v-if="result" class="bg-white rounded-lg border border-stone-200 p-4 space-y-4">
          <div class="grid grid-cols-3 gap-4">
            <Card class="shadow-sm"
              ><template #content
                ><div class="text-sm text-stone-500">待分配总额</div>
                <div class="text-xl font-bold text-stone-800">
                  ¥{{ result.total_proceeds?.toLocaleString() }}
                </div></template
              ></Card
            >
            <Card class="shadow-sm"
              ><template #content
                ><div class="text-sm text-stone-500">GP 合计</div>
                <div class="text-xl font-bold text-indigo-600">¥{{ result.gp_total?.toLocaleString() }}</div></template
              ></Card
            >
            <Card class="shadow-sm"
              ><template #content
                ><div class="text-sm text-stone-500">LP 合计</div>
                <div class="text-xl font-bold text-emerald-600">¥{{ result.lp_total?.toLocaleString() }}</div></template
              ></Card
            >
          </div>

          <h4 class="font-semibold text-zinc-700">分配明细</h4>
          <DataTable :value="result.steps" stripedRows size="small">
            <Column field="order" header="层级" />
            <Column field="name" header="名称" />
            <Column header="分配金额"
              ><template #body="{ data }">¥{{ data.allocated?.toLocaleString() }}</template></Column
            >
            <Column header="GP"
              ><template #body="{ data }">¥{{ data.gp_share?.toLocaleString() }}</template></Column
            >
            <Column header="LP"
              ><template #body="{ data }">¥{{ data.lp_share?.toLocaleString() }}</template></Column
            >
            <Column header="剩余"
              ><template #body="{ data }">¥{{ data.remaining?.toLocaleString() }}</template></Column
            >
          </DataTable>
        </div>
      </div>
    </div>

    <!-- Config Dialog -->
    <Dialog v-model:visible="showConfigDialog" header="新建瀑布配置" :style="{ width: '520px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div>
          <label class="text-sm text-stone-600">名称 *</label
          ><InputText v-model="configForm.name" class="w-full" placeholder="如 标准四层瀑布" />
        </div>
        <div>
          <label class="text-sm text-stone-600">关联组合</label
          ><Dropdown
            v-model="configForm.portfolio_id"
            :options="portfolios"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
          />
        </div>
        <div class="text-sm font-medium text-stone-600 mt-2">层级配置 ({{ configForm.tiers.length }})</div>
        <div v-for="(t, i) in configForm.tiers" :key="i" class="bg-stone-50 rounded p-3 space-y-2">
          <div class="flex gap-2 items-center">
            <span class="text-xs text-stone-400">#{{ t.order }}</span>
            <InputText v-model="t.name" class="flex-1" size="small" placeholder="层级名称" />
            <Dropdown
              v-model="t.type"
              :options="TIER_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-40"
              size="small"
            />
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="text-xs text-stone-400">门槛%</label
              ><InputNumber v-model="t.threshold_pct" class="w-full" size="small" suffix="%" />
            </div>
            <div>
              <label class="text-xs text-stone-400">GP%</label
              ><InputNumber v-model="t.gp_share_pct" class="w-full" size="small" suffix="%" />
            </div>
            <div>
              <label class="text-xs text-stone-400">LP%</label
              ><InputNumber v-model="t.lp_share_pct" class="w-full" size="small" suffix="%" />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showConfigDialog = false" />
        <Button label="保存" @click="saveConfig" :disabled="!configForm.name" />
      </template>
    </Dialog>
  </div>
</template>
