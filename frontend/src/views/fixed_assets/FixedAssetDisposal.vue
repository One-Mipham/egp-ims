<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, disposeFixedAsset } from '../../api'

const { t } = useI18n()
const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const statusFilter = ref('')
const dialogVisible = ref(false)
const selectedItem = ref<any>(null)
const disposalDate = ref('')
const disposalProceeds = ref(0)
const disposalReason = ref('')
const disposalType = ref('已处置')

const filteredItems = computed(() => {
  if (!statusFilter.value) return items.value
  return items.value.filter((i: any) => i.status === statusFilter.value)
})

async function load() {
  const { data } = await listFixedAssets(companyId)
  items.value = data
}

function openDisposal(row: any) {
  selectedItem.value = row
  disposalDate.value = new Date().toISOString().slice(0, 10)
  disposalProceeds.value = 0
  disposalReason.value = ''
  disposalType.value = '已处置'
  dialogVisible.value = true
}

async function confirmDisposal() {
  await disposeFixedAsset(selectedItem.value.id, {
    disposal_date: disposalDate.value,
    disposal_proceeds: disposalProceeds.value,
    disposal_reason: disposalReason.value,
    status: disposalType.value,
  })
  toast.add({ severity: 'success', summary: '处置完成', life: 2000 })
  dialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">{{ t('assets.disposeAsset') }}</h1>
      <select v-model="statusFilter" class="border rounded px-2 py-1 text-sm">
        <option value="">全部状态</option>
        <option value="使用中">使用中</option>
        <option value="闲置">闲置</option>
        <option value="已处置">已处置</option>
        <option value="报废">报废</option>
      </select>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">{{ t('assets.assetCode') }}</th>
          <th class="p-2 border">{{ t('common.name') }}</th>
          <th class="p-2 border">{{ t('assets.assetCategory') }}</th>
          <th class="p-2 border text-right">{{ t('assets.originalValue') }}</th>
          <th class="p-2 border text-right">{{ t('assets.netValue') }}</th>
          <th class="p-2 border">{{ t('common.status') }}</th>
          <th class="p-2 border">存放地点</th>
          <th class="p-2 border">{{ t('common.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in filteredItems"
          :key="item.id"
          class="hover:bg-zinc-50"
          :class="item.status === '已处置' || item.status === '报废' ? 'opacity-50' : ''"
        >
          <td class="p-2 border font-mono text-xs">{{ item.asset_code }}</td>
          <td class="p-2 border">{{ item.name }}</td>
          <td class="p-2 border text-xs">{{ item.category }}</td>
          <td class="p-2 border text-right">{{ (item.original_value || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.net_value || 0).toLocaleString() }}</td>
          <td class="p-2 border">
            <span
              :class="
                item.status === '使用中'
                  ? 'text-green-600'
                  : item.status === '已处置'
                    ? 'text-zinc-400'
                    : 'text-red-500'
              "
              >{{ item.status }}</span
            >
          </td>
          <td class="p-2 border text-xs">{{ item.location }}</td>
          <td class="p-2 border">
            <button
              v-if="item.status !== '已处置' && item.status !== '报废'"
              @click="openDisposal(item)"
              class="text-orange-600 text-xs"
            >
              处置
            </button>
            <span v-else class="text-xs text-zinc-400">--</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[440px] p-6">
        <h2 class="text-lg font-bold mb-4">资产处置 - {{ selectedItem?.name }}</h2>
        <div class="bg-zinc-50 rounded p-3 mb-3 text-sm">
          <div class="flex justify-between">
            <span>{{ t('assets.originalValue') }}</span><span>{{ (selectedItem?.original_value || 0).toLocaleString() }}</span>
          </div>
          <div class="flex justify-between">
            <span>{{ t('assets.accumulatedDepreciation') }}</span><span>{{ (selectedItem?.accumulated_depreciation || 0).toLocaleString() }}</span>
          </div>
          <div class="flex justify-between">
            <span>{{ t('assets.netValue') }}</span><span class="font-bold">{{ (selectedItem?.net_value || 0).toLocaleString() }}</span>
          </div>
          <div v-if="disposalProceeds > 0" class="flex justify-between mt-1 pt-1 border-t">
            <span>预计处置损益</span
            ><span
              :class="disposalProceeds - (selectedItem?.net_value || 0) >= 0 ? 'text-green-600' : 'text-red-500'"
              >{{ (disposalProceeds - (selectedItem?.net_value || 0)).toLocaleString() }}</span
            >
          </div>
        </div>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">处置类型</label>
            <select v-model="disposalType" class="w-full border rounded px-2 py-1.5 text-sm">
              <option value="已处置">已处置</option>
              <option value="报废">报废</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">处置日期</label
            ><input type="date" v-model="disposalDate" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">处置收入</label
            ><input type="number" v-model.number="disposalProceeds" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">处置原因</label
            ><textarea v-model="disposalReason" rows="2" class="w-full border rounded px-2 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">{{ t('common.cancel') }}</button>
          <button @click="confirmDisposal" class="px-4 py-1.5 bg-orange-600 text-white rounded text-sm">
            确认处置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
