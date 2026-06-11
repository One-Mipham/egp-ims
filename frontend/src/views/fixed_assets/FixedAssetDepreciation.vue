<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listDepreciations, createDepreciation, updateDepreciation, deleteDepreciation, batchDepreciate, listFixedAssets } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const assets = ref<any[]>([])
const dialogVisible = ref(false)
const batchDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editId = ref<number | null>(null)
const editAmount = ref(0)

const emptyForm = () => ({
  company_id: companyId, fixed_asset_id: null as number | null, period: '',
  depreciation_amount: 0,
})

const form = ref(emptyForm())
const batchPeriod = ref('')
const selectedAsset = ref<any>(null)
const page = ref(1)
const pageSize = 20

function assetName(id: number) {
  const a = assets.value.find((x: any) => x.id === id)
  return a ? `${a.asset_code} ${a.name}` : `#${id}`
}

async function load() {
  const [r1, r2] = await Promise.all([
    listDepreciations(companyId, { limit: pageSize, offset: (page.value - 1) * pageSize }),
    listFixedAssets(companyId)
  ])
  items.value = r1.data
  assets.value = r2.data
}

function openCreate() {
  form.value = emptyForm()
  selectedAsset.value = null
  dialogVisible.value = true
}

function onAssetChange() {
  const a = assets.value.find((x: any) => x.id === form.value.fixed_asset_id)
  selectedAsset.value = a || null
  form.value.depreciation_amount = 0
}

async function save() {
  await createDepreciation(form.value)
  toast.add({ severity: 'success', summary: '折旧已计提', life: 2000 })
  dialogVisible.value = false
  await load()
}

function openEdit(row: any) {
  editId.value = row.id
  editAmount.value = row.depreciation_amount
  editDialogVisible.value = true
}

async function saveEdit() {
  const row = items.value.find((i: any) => i.id === editId.value)
  if (!row) return
  await updateDepreciation(editId.value!, {
    company_id: row.company_id,
    fixed_asset_id: row.fixed_asset_id,
    period: row.period,
    depreciation_amount: editAmount.value,
  })
  toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  editDialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除该折旧记录？将恢复资产净值。')) {
    await deleteDepreciation(id)
    toast.add({ severity: 'success', summary: '已删除并恢复净值', life: 2000 })
    await load()
  }
}

async function runBatch() {
  if (!batchPeriod.value) return
  const res = await batchDepreciate({ company_id: companyId, period: batchPeriod.value })
  const { success, failed } = res.data
  toast.add({ severity: 'success', summary: `批量计提完成：成功${success.length}条，跳过${failed.length}条`, life: 4000 })
  batchDialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">折旧管理</h1>
      <div class="flex gap-2">
        <button @click="batchDialogVisible = true" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">批量计提</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 计提折旧</button>
      </div>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">资产</th><th class="p-2 border">期间</th>
          <th class="p-2 border text-right">本期折旧</th><th class="p-2 border text-right">计提前累计</th><th class="p-2 border text-right">计提后累计</th>
          <th class="p-2 border text-xs text-zinc-400">计提时间</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ assetName(item.fixed_asset_id) }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.period }}</td>
          <td class="p-2 border text-right">{{ (item.depreciation_amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_before || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_after || 0).toLocaleString() }}</td>
          <td class="p-2 border text-xs text-zinc-400">{{ item.created_at?.slice(0, 10) }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-2 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="7" class="p-6 text-center text-zinc-400 text-sm">暂无折旧记录</td>
        </tr>
      </tbody>
    </table>

    <div class="flex items-center justify-between mt-3">
      <span class="text-xs text-zinc-400">第 {{ page }} 页</span>
      <div class="flex gap-1">
        <button @click="page = Math.max(1, page - 1); load()" :disabled="page <= 1" class="px-3 py-1 border rounded text-sm disabled:opacity-30">上一页</button>
        <button @click="page = page + 1; load()" class="px-3 py-1 border rounded text-sm">下一页</button>
      </div>
    </div>

    <!-- 单项计提 -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[480px] p-6">
        <h2 class="text-lg font-bold mb-4">计提折旧</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">选择资产</label>
            <select v-model.number="form.fixed_asset_id" @change="onAssetChange" class="w-full border rounded px-2 py-1.5 text-sm">
              <option :value="null" disabled>-- 请选择 --</option>
              <option v-for="a in assets.filter((x: any) => x.status === '使用中' || x.status === '闲置')" :key="a.id" :value="a.id">{{ a.asset_code }} {{ a.name }} (净值 {{ (a.net_value || 0).toLocaleString() }})</option>
            </select>
          </div>
          <div v-if="selectedAsset" class="bg-zinc-50 rounded p-3 text-xs space-y-1">
            <div class="flex justify-between"><span class="text-zinc-500">原值</span><span>{{ (selectedAsset.original_value || 0).toLocaleString() }}</span></div>
            <div class="flex justify-between"><span class="text-zinc-500">累计折旧</span><span>{{ (selectedAsset.accumulated_depreciation || 0).toLocaleString() }}</span></div>
            <div class="flex justify-between"><span class="text-zinc-500">残值</span><span>{{ (selectedAsset.residual_value || 0).toLocaleString() }}</span></div>
          </div>
          <div><label class="text-xs text-zinc-500">折旧期间</label><input v-model="form.period" placeholder="YYYY-MM" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">折旧金额</label><input type="number" v-model.number="form.depreciation_amount" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">确认计提</button>
        </div>
      </div>
    </div>

    <!-- 批量计提 -->
    <div v-if="batchDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">批量计提折旧</h2>
        <p class="text-xs text-zinc-500 mb-3">将为所有"使用中"和"闲置"状态的资产计提折旧。已在该期间计提过的资产将自动跳过。</p>
        <div class="space-y-3">
          <div><label class="text-xs text-zinc-500">折旧期间</label><input v-model="batchPeriod" placeholder="YYYY-MM" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="batchDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="runBatch" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">执行批量计提</button>
        </div>
      </div>
    </div>

    <!-- 编辑折旧 -->
    <div v-if="editDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">修改折旧金额</h2>
        <div><label class="text-xs text-zinc-500">折旧金额</label><input type="number" v-model.number="editAmount" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="editDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="saveEdit" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
