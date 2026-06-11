<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { getContract } from '@/api/contracts'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const contract = ref<any>(null)
const loading = ref(true)

const typeLabels: Record<string, string> = {
  supplier: '供应商合同', customer: '客户合同', labor: '劳动合同', lease: '租赁合同',
}

function fmtDate(v: string) {
  if (!v) return '____年__月__日'
  if (v.length === 10) {
    const [y, m, d] = v.split('-')
    return `${y}年${parseInt(m)}月${parseInt(d)}日`
  }
  return v
}

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    const { data } = await getContract(id)
    contract.value = data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.message, life: 3000 })
  } finally { loading.value = false }
})

function doPrint() {
  window.print()
}
</script>

<template>
  <div v-if="loading" class="flex justify-center p-12"><i class="pi pi-spin pi-spinner text-3xl" /></div>

  <div v-else-if="contract" class="max-w-4xl mx-auto p-6">
    <!-- Print toolbar -->
    <div class="flex gap-2 mb-4 print:hidden">
      <Button label="打印合同" icon="pi pi-print" @click="doPrint" />
      <Button label="返回" severity="secondary" icon="pi pi-arrow-left" @click="router.back()" />
    </div>

    <!-- Contract Document A4 -->
    <div class="bg-white border shadow-lg p-10 print:shadow-none print:border-none print:p-0"
      style="min-height: 29.7cm; font-family: SimSun, serif; font-size: 14pt; line-height: 2;">

      <!-- Title -->
      <h1 class="text-center font-bold text-2xl mb-2" style="font-family: SimHei, sans-serif;">
        {{ contract.contract_name || contract.subject || '合同' }}
      </h1>

      <!-- Contract No -->
      <p class="text-right text-sm mb-4">合同编号：{{ contract.contract_no }}</p>

      <!-- Parties -->
      <div class="mb-6">
        <p><strong>甲方：</strong>{{ contract.party_a || '____________________' }}</p>
        <p>地址：{{ contract.party_a_address || '____________________' }}</p>
        <p>电话：{{ contract.party_a_phone || '____________________' }}</p>
        <p>法定代表人：{{ contract.party_a_representative || '____________________' }}</p>
        <p>授权签字人：{{ contract.party_a_signatory || '____________________' }}</p>
      </div>

      <div class="mb-6">
        <p><strong>乙方：</strong>{{ contract.party_b || '____________________' }}</p>
        <p>地址：{{ contract.party_b_address || '____________________' }}</p>
        <p>电话：{{ contract.party_b_phone || '____________________' }}</p>
        <p>法定代表人：{{ contract.party_b_representative || '____________________' }}</p>
        <p>授权签字人：{{ contract.party_b_signatory || '____________________' }}</p>
      </div>

      <!-- Whereas -->
      <p v-if="contract.legal_basis" class="mb-4 text-justify indent-8">
        根据<strong>《{{ contract.legal_basis.split(',').join('》、《') }}》</strong>及相关法律法规的规定，
        甲乙双方在平等、自愿、公平和诚实信用的基础上，经协商一致，就{{ contract.subject || '相关事宜' }}达成如下协议，以资共同遵守：
      </p>
      <p v-else class="mb-4 text-justify indent-8">
        根据《中华人民共和国民法典》及相关法律法规的规定，
        甲乙双方在平等、自愿、公平和诚实信用的基础上，经协商一致，就{{ contract.subject || '相关事宜' }}达成如下协议，以资共同遵守：
      </p>

      <!-- Main Clauses -->
      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">一、合同标的</h2>
        <p class="indent-8 text-justify">{{ contract.subject || '（双方应根据实际情况填写合同标的的具体内容、范围及要求。）' }}</p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">二、合同金额与支付条款</h2>
        <p class="indent-8">合同总金额：<strong>¥{{ contract.amount?.toLocaleString() || '0' }}</strong>（人民币）</p>
        <div v-if="contract.payment_terms" class="indent-8 text-justify whitespace-pre-wrap">{{ contract.payment_terms }}</div>
        <p v-else class="indent-8 text-gray-500">（财务支付条款待填写...）</p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">三、合同期限</h2>
        <p class="indent-8">本合同自 <strong>{{ fmtDate(contract.start_date) }}</strong> 起生效，
        至 <strong>{{ fmtDate(contract.end_date) }}</strong> 止。</p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">四、双方权利与义务</h2>
        <p class="indent-8">（双方应根据实际情况约定具体权利与义务条款。）</p>
      </div>

      <div v-if="contract.force_majeure" class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">五、不可抗力</h2>
        <div class="indent-8 text-justify whitespace-pre-wrap">{{ contract.force_majeure }}</div>
      </div>
      <div v-else class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">五、不可抗力</h2>
        <p class="indent-8 text-justify">
          因不可抗力导致本合同无法履行或不能完全履行的，遭遇不可抗力的一方应在不可抗力事件发生后
          <strong>____</strong>日内书面通知对方，并提供相关证明。双方协商一致后可解除合同或延期履行，
          任何一方不得因此向对方主张违约赔偿。不可抗力是指不能预见、不能避免并不能克服的客观情况。
        </p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">六、违约责任</h2>
        <p class="indent-8">（双方应根据实际情况约定违约责任条款。）</p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">七、争议解决</h2>
        <p v-if="contract.arbitration_venue" class="indent-8">
          因本合同引起的或与本合同有关的任何争议，双方应友好协商解决；协商不成的，
          任何一方均有权向<strong> {{ contract.arbitration_venue }} </strong>提起诉讼/申请仲裁。
        </p>
        <p v-else class="indent-8">
          因本合同引起的或与本合同有关的任何争议，双方应友好协商解决；协商不成的，
          任何一方均有权向<strong> 合同签订地有管辖权的人民法院 </strong>提起诉讼。
        </p>
      </div>

      <div class="mb-4">
        <h2 class="font-bold text-lg mb-2" style="font-family: SimHei, sans-serif;">八、其他约定</h2>
        <p v-if="contract.notes" class="indent-8 text-justify whitespace-pre-wrap">{{ contract.notes }}</p>
        <p v-else class="indent-8">
          本合同一式 <strong>____</strong> 份，甲方持 <strong>____</strong> 份，乙方持 <strong>____</strong> 份，
          自双方签字盖章之日起生效。未尽事宜，双方可另行签订补充协议，补充协议与本合同具有同等法律效力。
        </p>
      </div>

      <!-- Signatures -->
      <div class="mt-12 grid grid-cols-2 gap-8">
        <div>
          <p class="font-bold">甲方（盖章）：{{ contract.party_a || '____________________' }}</p>
          <p class="mt-4">授权签字人：{{ contract.party_a_signatory || '____________________' }}</p>
          <p class="mt-4">日期：____年____月____日</p>
        </div>
        <div>
          <p class="font-bold">乙方（盖章）：{{ contract.party_b || '____________________' }}</p>
          <p class="mt-4">授权签字人：{{ contract.party_b_signatory || '____________________' }}</p>
          <p class="mt-4">日期：____年____月____日</p>
        </div>
      </div>

      <p class="mt-8 text-center text-sm">签署日期：{{ fmtDate(contract.sign_date) }}</p>
    </div>
  </div>
</template>

<style scoped>
@media print {
  .print\:hidden { display: none !important; }
  .print\:shadow-none { box-shadow: none !important; }
  .print\:border-none { border: none !important; }
  .print\:p-0 { padding: 0 !important; }
  body { margin: 0; padding: 0; }
}
</style>
