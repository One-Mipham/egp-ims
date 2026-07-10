<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import {
  listServers,
  createServer,
  updateServer,
  deleteServer,
  listServices,
  createService,
  updateService,
  deleteService,
  controlService,
} from '../api'

const toast = useToast()
const confirm = useConfirm()
const companyId = Number(localStorage.getItem('companyId') || '1')

// ── Tab state ──
const activeTab = ref<'servers' | 'services'>('servers')

// ── Server state ──
const servers = ref<any[]>([])
const serverLoading = ref(false)
const serverDialog = ref(false)
const serverForm = ref<any>({
  name: '',
  host: '',
  port: null,
  os: '',
  cpu_cores: null,
  memory_gb: null,
  disk_gb: null,
  location: '',
  description: '',
})
const editingServerId = ref<number | null>(null)

// ── Service state ──
const selectedServerId = ref<number | null>(null)
const services = ref<any[]>([])
const serviceLoading = ref(false)
const serviceDialog = ref(false)
const serviceForm = ref<any>({
  name: '',
  description: '',
  service_type: 'application',
  port: null,
  health_check_url: '',
  process_name: '',
  auto_start: false,
  notes: '',
})
const editingServiceId = ref<number | null>(null)
const controllingServiceId = ref<number | null>(null)

const serviceTypeOptions = [
  { label: 'ITS服务', value: 'its' },
  { label: '应用服务', value: 'application' },
  { label: '任务服务', value: 'task' },
  { label: '更新服务', value: 'update' },
  { label: '数据库服务', value: 'database' },
  { label: '网关服务', value: 'gateway' },
  { label: '监控服务', value: 'monitoring' },
  { label: '其他', value: 'other' },
]

const serverOptions = computed(() => servers.value.map((s: any) => ({ label: s.name, value: s.id })))

// ── Server CRUD ──
async function loadServers() {
  serverLoading.value = true
  try {
    servers.value = (await listServers(companyId)).data
  } finally {
    serverLoading.value = false
  }
}

function openServerDialog(srv?: any) {
  if (srv) {
    editingServerId.value = srv.id
    serverForm.value = {
      name: srv.name,
      host: srv.host || '',
      port: srv.port,
      os: srv.os || '',
      cpu_cores: srv.cpu_cores,
      memory_gb: srv.memory_gb,
      disk_gb: srv.disk_gb,
      location: srv.location || '',
      description: srv.description || '',
    }
  } else {
    editingServerId.value = null
    serverForm.value = {
      name: '',
      host: '',
      port: null,
      os: '',
      cpu_cores: null,
      memory_gb: null,
      disk_gb: null,
      location: '',
      description: '',
    }
  }
  serverDialog.value = true
}

async function saveServer() {
  const data = { ...serverForm.value, company_id: companyId }
  if (editingServerId.value) {
    await updateServer(editingServerId.value, data)
    toast.add({ severity: 'success', summary: '服务器已更新', life: 2000 })
  } else {
    await createServer(data)
    toast.add({ severity: 'success', summary: '服务器已添加', life: 2000 })
  }
  serverDialog.value = false
  loadServers()
}

function confirmDeleteServer(srv: any) {
  confirm.require({
    message: `确认删除服务器 ${srv.name}？其下的所有服务也将被删除。`,
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await deleteServer(srv.id)
      toast.add({ severity: 'success', summary: '服务器已删除', life: 2000 })
      loadServers()
    },
  })
}

// ── Service CRUD ──
async function selectServer(id: number) {
  selectedServerId.value = id
  await loadServices()
}

async function loadServices() {
  if (!selectedServerId.value) return
  serviceLoading.value = true
  try {
    services.value = (await listServices(selectedServerId.value)).data
  } finally {
    serviceLoading.value = false
  }
}

function openServiceDialog(svc?: any) {
  if (svc) {
    editingServiceId.value = svc.id
    serviceForm.value = {
      name: svc.name,
      description: svc.description || '',
      service_type: svc.service_type,
      port: svc.port,
      health_check_url: svc.health_check_url || '',
      process_name: svc.process_name || '',
      auto_start: svc.auto_start,
      notes: svc.notes || '',
    }
  } else {
    editingServiceId.value = null
    serviceForm.value = {
      name: '',
      description: '',
      service_type: 'application',
      port: null,
      health_check_url: '',
      process_name: '',
      auto_start: false,
      notes: '',
    }
  }
  serviceDialog.value = true
}

async function saveService() {
  if (!selectedServerId.value) return
  const data = { ...serviceForm.value, server_id: selectedServerId.value }
  if (editingServiceId.value) {
    await updateService(editingServiceId.value, data)
    toast.add({ severity: 'success', summary: '服务已更新', life: 2000 })
  } else {
    await createService(selectedServerId.value, data)
    toast.add({ severity: 'success', summary: '服务已添加', life: 2000 })
  }
  serviceDialog.value = false
  loadServices()
}

function confirmDeleteService(svc: any) {
  confirm.require({
    message: `确认删除服务 ${svc.name}？`,
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await deleteService(svc.id)
      toast.add({ severity: 'success', summary: '服务已删除', life: 2000 })
      loadServices()
    },
  })
}

async function doControl(svc: any, action: 'start' | 'stop' | 'restart') {
  controllingServiceId.value = svc.id
  try {
    await controlService(svc.id, action)
    toast.add({
      severity: 'success',
      summary: `服务${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'}成功`,
      life: 2000,
    })
    loadServices()
  } finally {
    controllingServiceId.value = null
  }
}

function statusSeverity(status: string) {
  switch (status) {
    case 'running':
      return 'success'
    case 'stopped':
      return 'danger'
    case 'error':
      return 'danger'
    case 'starting':
    case 'stopping':
      return 'warn'
    default:
      return 'secondary'
  }
}
function statusLabel(status: string) {
  switch (status) {
    case 'running':
      return '运行中'
    case 'stopped':
      return '已停止'
    case 'error':
      return '异常'
    case 'starting':
      return '启动中'
    case 'stopping':
      return '停止中'
    default:
      return status
  }
}
function serverStatusLabel(status: string) {
  switch (status) {
    case 'active':
      return '正常'
    case 'inactive':
      return '离线'
    case 'maintenance':
      return '维护中'
    default:
      return status
  }
}
function serverStatusSeverity(status: string) {
  switch (status) {
    case 'active':
      return 'success'
    case 'inactive':
      return 'danger'
    case 'maintenance':
      return 'warn'
    default:
      return 'secondary'
  }
}

onMounted(loadServers)
</script>

<template>
  <div>
    <Toast />
    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6">
      <!-- Tab bar -->
      <div class="flex gap-0 mb-6 border-b border-zinc-200">
        <button
          class="px-5 py-2.5 text-sm font-medium rounded-t-sm transition-colors"
          :class="
            activeTab === 'servers'
              ? 'bg-white text-blue-600 border-b-2 border-blue-600 -mb-px'
              : 'text-zinc-500 hover:text-zinc-700'
          "
          @click="activeTab = 'servers'"
        >
          <i class="pi pi-server mr-1.5" />服务器列表
        </button>
        <button
          class="px-5 py-2.5 text-sm font-medium rounded-t-sm transition-colors"
          :class="
            activeTab === 'services'
              ? 'bg-white text-blue-600 border-b-2 border-blue-600 -mb-px'
              : 'text-zinc-500 hover:text-zinc-700'
          "
          @click="activeTab = 'services'"
        >
          <i class="pi pi-cog mr-1.5" />服务管理
        </button>
      </div>

      <!-- ═══════════ Tab: 服务器列表 ═══════════ -->
      <div v-if="activeTab === 'servers'">
        <div class="flex justify-between items-center mb-4">
          <p class="text-sm text-zinc-500">管理物理/虚拟服务器，添加服务器后方可在「服务管理」中配置运行服务</p>
          <Button label="添加服务器" icon="pi pi-plus" size="small" @click="openServerDialog()" />
        </div>
        <DataTable
          :value="servers"
          :loading="serverLoading"
          stripedRows
          class="shadow-sm"
          tableStyle="min-width: auto"
          paginator
          :rows="10"
          :rowsPerPageOptions="[5, 10, 20]"
        >
          <Column field="name" header="服务器名称" style="width: 140px" />
          <Column field="host" header="主机地址" style="width: 140px" />
          <Column field="os" header="操作系统" style="width: 100px" />
          <Column field="cpu_cores" header="CPU核" style="width: 70px" />
          <Column header="内存/磁盘" style="width: 120px">
            <template #body="{ data }">
              {{ data.memory_gb ? data.memory_gb + 'GB' : '-' }} / {{ data.disk_gb ? data.disk_gb + 'GB' : '-' }}
            </template>
          </Column>
          <Column field="location" header="位置" style="width: 90px" />
          <Column header="状态" style="width: 70px">
            <template #body="{ data }">
              <Tag :value="serverStatusLabel(data.status)" :severity="serverStatusSeverity(data.status)" />
            </template>
          </Column>
          <Column header="操作" style="width: 120px">
            <template #body="{ data }">
              <Button icon="pi pi-pencil" text size="small" @click="openServerDialog(data)" v-tooltip.top="'编辑'" />
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                @click="confirmDeleteServer(data)"
                v-tooltip.top="'删除'"
              />
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- ═══════════ Tab: 服务管理 ═══════════ -->
      <div v-if="activeTab === 'services'">
        <div class="flex justify-between items-center mb-4">
          <div class="flex items-center gap-3">
            <label class="text-sm text-zinc-600 font-medium">选择服务器：</label>
            <Dropdown
              v-model="selectedServerId"
              :options="serverOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="请选择服务器"
              class="w-48"
              @change="(e: any) => selectServer(e.value)"
            />
          </div>
          <Button
            v-if="selectedServerId"
            label="添加服务"
            icon="pi pi-plus"
            size="small"
            @click="openServiceDialog()"
          />
        </div>

        <div v-if="!selectedServerId" class="text-center py-12 text-zinc-400">
          <i class="pi pi-arrow-up text-3xl block mb-3" />
          请先选择一个服务器，再管理其运行的服务
        </div>

        <DataTable
          v-else
          :value="services"
          :loading="serviceLoading"
          stripedRows
          class="shadow-sm"
          tableStyle="min-width: auto"
        >
          <Column field="name" header="服务名称" style="width: 120px" />
          <Column field="description" header="描述" style="width: 150px" />
          <Column header="服务类型" style="width: 90px">
            <template #body="{ data }">
              <Tag
                :value="serviceTypeOptions.find(o => o.value === data.service_type)?.label || data.service_type"
                severity="info"
              />
            </template>
          </Column>
          <Column header="状态" style="width: 70px">
            <template #body="{ data }">
              <Tag :value="statusLabel(data.status)" :severity="statusSeverity(data.status)" />
            </template>
          </Column>
          <Column field="port" header="端口" style="width: 60px" />
          <Column header="启停控制" style="width: 180px">
            <template #body="{ data }">
              <div class="flex gap-1">
                <Button
                  icon="pi pi-play"
                  text
                  size="small"
                  severity="success"
                  :loading="controllingServiceId === data.id"
                  :disabled="data.status === 'running'"
                  @click="doControl(data, 'start')"
                  v-tooltip.top="'启动'"
                />
                <Button
                  icon="pi pi-stop"
                  text
                  size="small"
                  severity="danger"
                  :loading="controllingServiceId === data.id"
                  :disabled="data.status === 'stopped'"
                  @click="doControl(data, 'stop')"
                  v-tooltip.top="'停止'"
                />
                <Button
                  icon="pi pi-refresh"
                  text
                  size="small"
                  severity="warn"
                  :loading="controllingServiceId === data.id"
                  @click="doControl(data, 'restart')"
                  v-tooltip.top="'重启'"
                />
              </div>
            </template>
          </Column>
          <Column header="操作" style="width: 80px">
            <template #body="{ data }">
              <Button icon="pi pi-pencil" text size="small" @click="openServiceDialog(data)" v-tooltip.top="'编辑'" />
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                @click="confirmDeleteService(data)"
                v-tooltip.top="'删除'"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <!-- ═══════════ Server Dialog ═══════════ -->
    <Dialog
      v-model:visible="serverDialog"
      :header="editingServerId ? '编辑服务器' : '添加服务器'"
      :modal="true"
      class="w-[480px]"
      :dismissableMask="true"
    >
      <div class="flex flex-col gap-3 pt-2">
        <div>
          <label class="text-sm text-zinc-600">名称 *</label><InputText v-model="serverForm.name" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-zinc-600">主机地址</label
          ><InputText v-model="serverForm.host" class="w-full" placeholder="IP 或域名" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-zinc-600">端口</label
            ><InputText v-model="serverForm.port" class="w-full" type="number" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">操作系统</label
            ><InputText v-model="serverForm.os" class="w-full" placeholder="如 Ubuntu 22.04" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="text-sm text-zinc-600">CPU核数</label
            ><InputText v-model="serverForm.cpu_cores" class="w-full" type="number" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">内存(GB)</label
            ><InputText v-model="serverForm.memory_gb" class="w-full" type="number" step="0.5" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">磁盘(GB)</label
            ><InputText v-model="serverForm.disk_gb" class="w-full" type="number" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-zinc-600">位置/区域</label
            ><InputText v-model="serverForm.location" class="w-full" placeholder="如 北京/阿里云" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">状态</label>
            <Dropdown
              v-model="serverForm.status"
              :options="[
                { label: '正常', value: 'active' },
                { label: '离线', value: 'inactive' },
                { label: '维护中', value: 'maintenance' },
              ]"
              class="w-full"
              v-if="editingServerId"
            />
            <InputText value="正常（默认）" class="w-full" disabled v-else />
          </div>
        </div>
        <div>
          <label class="text-sm text-zinc-600">描述</label><InputText v-model="serverForm.description" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" text @click="serverDialog = false" />
        <Button label="保存" icon="pi pi-check" @click="saveServer" :disabled="!serverForm.name" />
      </template>
    </Dialog>

    <!-- ═══════════ Service Dialog ═══════════ -->
    <Dialog
      v-model:visible="serviceDialog"
      :header="editingServiceId ? '编辑服务' : '添加服务'"
      :modal="true"
      class="w-[480px]"
      :dismissableMask="true"
    >
      <div class="flex flex-col gap-3 pt-2">
        <div>
          <label class="text-sm text-zinc-600">服务名称 *</label><InputText v-model="serviceForm.name" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-zinc-600">描述</label
          ><InputText v-model="serviceForm.description" class="w-full" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-zinc-600">服务类型</label
            ><Dropdown v-model="serviceForm.service_type" :options="serviceTypeOptions" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">端口</label
            ><InputText v-model="serviceForm.port" class="w-full" type="number" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-zinc-600">健康检查URL</label
            ><InputText v-model="serviceForm.health_check_url" class="w-full" placeholder="/healthz" />
          </div>
          <div>
            <label class="text-sm text-zinc-600">进程/容器名</label
            ><InputText v-model="serviceForm.process_name" class="w-full" placeholder="docker容器名" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="serviceForm.auto_start" id="auto-start" class="w-4 h-4" />
          <label for="auto-start" class="text-sm text-zinc-600">开机自启</label>
        </div>
        <div>
          <label class="text-sm text-zinc-600">备注</label><InputText v-model="serviceForm.notes" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" text @click="serviceDialog = false" />
        <Button label="保存" icon="pi pi-check" @click="saveService" :disabled="!serviceForm.name" />
      </template>
    </Dialog>
  </div>
</template>
