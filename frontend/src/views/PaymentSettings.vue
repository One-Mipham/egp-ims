<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'

const toast = useToast()

const bankAccounts = ref<any[]>([])

const BANK_TYPE_OPTIONS = [
  { label: '银行账户', value: 'bank' },
  { label: '支付宝', value: 'alipay' },
  { label: '微信', value: 'wechat' },
]

onMounted(() => {
  const saved = localStorage.getItem('payment_accounts')
  if (saved) {
    bankAccounts.value = JSON.parse(saved)
  } else {
    bankAccounts.value = [
      { name: '工商银行基本户', account: '6222021234567890123', type: 'bank', is_default: true },
      { name: '支付宝账户', account: 'company@mipham.ai', type: 'alipay', is_default: false },
    ]
  }
})

function addAccount() {
  bankAccounts.value.push({ name: '', account: '', type: 'bank', is_default: false })
}

function removeAccount(idx: number) {
  bankAccounts.value.splice(idx, 1)
}

function saveAccounts() {
  localStorage.setItem('payment_accounts', JSON.stringify(bankAccounts.value))
  toast.add({ severity: 'success', summary: '已保存', life: 2000 })
}
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6 max-w-2xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-medium text-zinc-600">收付款账户</h3>
        <Button label="新增账户" icon="pi pi-plus" text size="small" @click="addAccount" />
      </div>
      <div v-for="(acct, idx) in bankAccounts" :key="idx" class="flex gap-3 items-end mb-3">
        <div class="flex-1">
          <label class="block text-xs text-zinc-500 mb-1">账户名称</label>
          <InputText v-model="acct.name" class="w-full" />
        </div>
        <div class="w-48">
          <label class="block text-xs text-zinc-500 mb-1">类型</label>
          <Dropdown v-model="acct.type" :options="BANK_TYPE_OPTIONS" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="flex-1">
          <label class="block text-xs text-zinc-500 mb-1">账号</label>
          <InputText v-model="acct.account" class="w-full" />
        </div>
        <Button icon="pi pi-trash" text severity="danger" size="small" @click="removeAccount(idx)" />
      </div>
      <div class="flex gap-2 pt-2">
        <Button label="保存" icon="pi pi-check" @click="saveAccounts" />
      </div>
    </div>
  </div>
</template>
