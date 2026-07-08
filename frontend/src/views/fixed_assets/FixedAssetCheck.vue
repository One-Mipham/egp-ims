<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, updateFixedAsset } from '../../api'

const { t } = useI18n()
const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const categoryFilter = ref('')
const locationFilter = ref('')
const editDialogVisible = ref(false)
const editItem = ref<any>(null)
const editLocation = ref('')
const editNotes = ref('')

const categories = computed(() => [...new Set(items.value.map((i: any) => i.category))])
const locations = computed(() => [...new Set(items.value.map((i: any) => i.location).filter(Boolean))])

const filteredItems = computed(() => {
  let result = items.value
  if (categoryFilter.value) result = result.filter((i: any) => i.category === categoryFilter.value)
  if (locationFilter.value) result = result.filter((i: any) => i.location === locationFilter.value)
  return result
})

const stats = computed(() => {
  const f = filteredItems.value
  return {
    count: f.length,
    totalOriginal: f.reduce((s: number, i: any) => s + (i.original_value || 0), 0),
    totalNet: f.reduce((s: number, i: any) => s + (i.net_value || 0), 0),
  }
})

async function load() {
  const { data } = await listFixedAssets(companyId)
  items.value = data
}

function openEdit(row: any) {
  editItem.value = row
  editLocation.value = row.location || ''
  editNotes.value = row.notes || ''
  editDialogVisible.value = true
}

async function saveEdit() {
  await updateFixedAsset(editItem.value.id, {
    ...editItem.value,
    location: editLocation.value,
    notes: editNotes.value,
  })
  toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  editDialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">资产盘点</h1>
      <div class="flex gap-2">
        <select v-model="categoryFilter" class="border rounded px-2 py-1 text-sm">
          <option value="">全部类别</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="locationFilter" class="border rounded px-2 py-1 text-sm">
          <option value="">全部地点</option>
          <option v-for="l in locations" :key="l" :value="l">{{ l }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3 mb-4">
      <div class="bg-zinc-50 rounded p-3 text-center">
        <div class="text-xs text-zinc-500">资产数量</div>
        <div class="text-lg font-bold">{{ stats.count }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-3 text-center">
        <div class="text-xs text-zinc-500">原值合计</div>
        <div class="text-lg font-bold">{{ stats.totalOriginal.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-3 text-center">
        <div class="text-xs text-zinc-500">净值合计</div>
        <div class="text-lg font-bold">{{ stats.totalNet.toLocaleString() }}</div>
      </div>
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
        <tr v-for="item in filteredItems" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono text-xs">{{ item.asset_code }}</td>
          <td class="p-2 border">{{ item.name }}</td>
          <td class="p-2 border text-xs">{{ item.category }}</td>
          <td class="p-2 border text-right">{{ (item.original_value || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.net_value || 0).toLocaleString() }}</td>
          <td class="p-2 border">
            <span :class="item.status === '使用中' ? 'text-green-600' : 'text-red-500'">{{ item.status }}</span>
          </td>
          <td class="p-2 border text-xs">{{ item.location }}</td>
          <td class="p-2 border"><button @click="openEdit(item)" class="text-blue-600 text-xs">盘点调整</button></td>
        </tr>
      </tbody>
    </table>

    <div v-if="editDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">盘点调整 - {{ editItem?.name }}</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">存放地点</label
            ><input v-model="editLocation" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">盘点备注</label
            ><textarea v-model="editNotes" rows="2" class="w-full border rounded px-2 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="editDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">{{ t('common.cancel') }}</button>
          <button @click="saveEdit" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">{{ t('common.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
