# Approval Bypass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add force-bypass endpoints and UI buttons so super_admin / finance_director can skip any approval node, preventing process deadlock.

**Architecture:** New `BypassAction` schema in schemas, `check_approval_bypass` in permissions, bypass endpoints in expenses/admin/bids routers, `BypassButton` conditional UI in 4 Vue components.

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / Vue 3 / PrimeVue

---

### Task 1: Add BypassAction schema

**Files:**
- Modify: `backend/app/schemas/__init__.py` (after `ApprovalAction` at L750)

- [ ] **Step 1: Add BypassAction schema**

```python
class BypassAction(BaseModel):
    reason: str  # 必填，强制跳过原因
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/__init__.py
git commit -m "feat: add BypassAction schema for approval bypass"
```

---

### Task 2: Add check_approval_bypass permission

**Files:**
- Modify: `backend/app/permissions.py` (append at end of file)

- [ ] **Step 1: Add bypass permission check**

```python
def check_approval_bypass(user) -> str | None:
    """仅超级管理员和财务总监可强制跳过审批节点"""
    if user.role in ("super_admin", "finance_director"):
        return None
    return "仅管理员和财务总监可强制跳过审批"
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/permissions.py
git commit -m "feat: add check_approval_bypass permission guard"
```

---

### Task 3: Add expense report bypass endpoint

**Files:**
- Modify: `backend/app/routers/expenses.py` (after `cancel_report` around L425)

- [ ] **Step 1: Import new dependencies at top of expenses.py**

Add to existing imports:
```python
from app.schemas import BypassAction
from app.permissions import check_approval_bypass
import json
```

- [ ] **Step 2: Add report bypass endpoint**

Add after the `cancel_report` function:

```python
@router.post("/reports/{report_id}/bypass", response_model=ExpenseReportResponse)
def bypass_report_approval(report_id: int, action: BypassAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """强制跳过当前审批节点（仅管理员/财务总监）"""
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")

    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    chain = report.approval_chain or []
    now_iso = datetime.utcnow().isoformat()
    bypassed_node = None

    # 标记当前 pending 节点为 bypassed
    for node in chain:
        if node["status"] == "pending":
            bypassed_node = {"role": node.get("role"), "user_id": node.get("user_id")}
            node["status"] = "bypassed"
            node["user_id"] = user.id
            node["comment"] = action.reason
            node["timestamp"] = now_iso
            break

    # 推进到下一个节点
    next_node = None
    for node in chain:
        if node["status"] == "pending":
            next_node = node
            break

    if next_node:
        report.current_approver_id = next_node.get("user_id")
    else:
        report.current_approver_id = None

    report.approval_chain = chain

    # 写入审计日志
    db.add(AuditLog(
        company_id=report.company_id, user_id=user.id,
        action="bypass_approval", target_type="expense_report",
        target_id=report.id, reason=action.reason,
        details=json.dumps({"bypassed_node": bypassed_node}),
    ))

    db.commit()
    db.refresh(report)
    return report
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/expenses.py
git commit -m "feat: add bypass endpoint for expense reports"
```

---

### Task 4: Add expense loan bypass endpoint

**Files:**
- Modify: `backend/app/routers/expenses.py` (after `approve_loan` around L466)

- [ ] **Step 1: Add loan bypass endpoint**

Add after the `approve_loan` function:

```python
@router.post("/loans/{loan_id}/bypass", response_model=ExpenseLoanResponse)
def bypass_loan_approval(loan_id: int, action: BypassAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """强制跳过借款审批（仅管理员/财务总监）"""
    loan = db.query(ExpenseLoan).filter(ExpenseLoan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款单不存在")

    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    if loan.status not in ("submitted", "draft"):
        raise HTTPException(status_code=400, detail="当前状态不可跳过审批")

    loan.status = "approved"

    # 写入审计日志
    db.add(AuditLog(
        company_id=loan.company_id, user_id=user.id,
        action="bypass_approval", target_type="expense_loan",
        target_id=loan.id, reason=action.reason,
    ))

    db.commit()
    db.refresh(loan)
    return loan
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/expenses.py
git commit -m "feat: add bypass endpoint for expense loans"
```

---

### Task 5: Add admin entity bypass endpoint

**Files:**
- Modify: `backend/app/routers/admin.py` (imports + after `_process_approval` around L96)

- [ ] **Step 1: Add import for BypassAction**

At top of admin.py, add:
```python
from app.schemas import BypassAction
```

- [ ] **Step 2: Add admin bypass endpoint**

Add a new bypass endpoint after the existing approve/reject endpoint:

```python
@router.post("/{target_type}/{target_id}/bypass-step")
def bypass_admin_step(
    target_type: str,
    target_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """强制跳过行政审批当前步骤（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    records = db.query(ApprovalRecord).filter(
        ApprovalRecord.target_type == target_type,
        ApprovalRecord.target_id == target_id,
    ).order_by(ApprovalRecord.step).all()

    if not records:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    current_step = None
    for r in records:
        if r.status == "pending":
            current_step = r
            break

    if current_step is None:
        raise HTTPException(status_code=400, detail="该审批流程已结束")

    current_step.status = "bypassed"
    current_step.comment = action.reason

    # 推进：检查是否还有待审批步骤
    remaining = any(r.status == "pending" for r in records if r.step > current_step.step)
    if not remaining:
        _update_entity_status(db, target_type, target_id, "approved")

    _write_audit(db, 0, user, "bypass_step", target_type, target_id, action.reason)

    db.commit()
    return {"ok": True, "bypassed": True}
```

- [ ] **Step 3: Add check_approval_bypass import**

At top of admin.py imports, add:
```python
from app.permissions import check_approval_bypass
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/admin.py
git commit -m "feat: add bypass-step endpoint for admin entities"
```

---

### Task 6: Add bids bypass endpoints

**Files:**
- Modify: `backend/app/routers/bids.py` (after `approve_tender_project` L189, after `approve_exception_event` L507)

- [ ] **Step 1: Add imports and tender project bypass**

At top of bids.py, add:
```python
from app.schemas import BypassAction
from app.permissions import check_approval_bypass
```

Add after `approve_tender_project`:

```python
@router.post("/tender-projects/{project_id}/bypass")
def bypass_tender_project(
    project_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """强制跳过招标项目审批（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")

    p.approver_id = user.id
    p.approved_at = datetime.utcnow()
    if p.status == "draft":
        p.status = "approved"

    db.add(AuditLog(
        company_id=getattr(p, "company_id", 0), user_id=user.id,
        action="bypass_approval", target_type="tender_project",
        target_id=p.id, reason=action.reason,
    ))
    db.commit()
    return {"ok": True, "bypassed": True}
```

- [ ] **Step 2: Add exception event bypass**

Add after `approve_exception_event`:

```python
@router.post("/exceptions/{event_id}/bypass")
def bypass_exception_event(
    event_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """强制跳过例外事项审批（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")

    e.approver_id = user.id
    e.approved_at = datetime.utcnow()
    e.status = "approved"

    db.add(AuditLog(
        company_id=getattr(e, "company_id", 0), user_id=user.id,
        action="bypass_approval", target_type="exception_event",
        target_id=e.id, reason=action.reason,
    ))
    db.commit()
    return {"ok": True, "bypassed": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/bids.py
git commit -m "feat: add bypass endpoints for tender projects and exception events"
```

---

### Task 7: Add frontend API functions

**Files:**
- Modify: `frontend/src/api/expenses.ts`
- Modify: `frontend/src/api/bids.ts`

- [ ] **Step 1: Add bypass API calls to expenses.ts**

Add at end of file:
```typescript
export const bypassReport = (id: number, reason: string) =>
  api.post(`/expenses/reports/${id}/bypass`, { reason })

export const bypassLoan = (id: number, reason: string) =>
  api.post(`/expenses/loans/${id}/bypass`, { reason })
```

- [ ] **Step 2: Add bypass API calls to bids.ts**

Add at end of file:
```typescript
export const bypassTenderProject = (id: number, reason: string) =>
  api.post(`/bids/tender-projects/${id}/bypass`, { reason })

export const bypassExceptionEvent = (id: number, reason: string) =>
  api.post(`/bids/exceptions/${id}/bypass`, { reason })
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/expenses.ts frontend/src/api/bids.ts
git commit -m "feat: add bypass API functions to frontend"
```

---

### Task 8: Add bypass button to ExpenseReportList

**Files:**
- Modify: `frontend/src/views/expenses/ExpenseReportList.vue`

- [ ] **Step 1: Import bypass API**

Add to import from `@/api/expenses`:
```typescript
import { listExpenseReports, approveReport, rejectReport, cancelReport, bypassReport } from '@/api/expenses'
```

- [ ] **Step 2: Add bypass state and user role check**

Add in `<script setup>`:
```typescript
const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')

const openBypass = (r: any) => { currentReport.value = r; bypassReason.value = ''; bypassDialog.value = true }

const doBypass = async () => {
  try {
    await bypassReport(currentReport.value.id, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; fetchReports()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}
```

- [ ] **Step 3: Add bypass button in template**

In the actions column (after the approve/reject buttons, around L122):
```html
<Button v-if="canBypass && slotProps.data.current_approver_id" icon="pi pi-forward" size="small" text rounded severity="warn" @click="openBypass(slotProps.data)" v-tooltip.top="'强制跳过'" />
```

- [ ] **Step 4: Add bypass dialog**

Add after the reject dialog (around L140):
```html
<Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
  <div class="flex flex-col gap-3">
    <p class="text-sm text-stone-600">您正在强制跳过审批节点，此操作将记录到审计日志。</p>
    <label class="form-label">跳过原因（必填）</label>
    <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
  </div>
  <template #footer>
    <Button label="取消" severity="secondary" @click="bypassDialog = false" />
    <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypass" />
  </template>
</Dialog>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/expenses/ExpenseReportList.vue
git commit -m "feat: add bypass button to ExpenseReportList"
```

---

### Task 9: Add bypass button to ExpenseLoanList

**Files:**
- Modify: `frontend/src/views/expenses/ExpenseLoanList.vue`

- [ ] **Step 1: Import bypass API and add logic**

Add to import:
```typescript
import { listExpenseLoans, createExpenseLoan, approveLoan, repayLoan, bypassLoan } from '@/api/expenses'
```

Add in `<script setup>`:
```typescript
const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentLoanId = ref<number | null>(null)

const openBypass = (id: number) => { currentLoanId.value = id; bypassReason.value = ''; bypassDialog.value = true }

const doBypass = async () => {
  try {
    await bypassLoan(currentLoanId.value!, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; fetchLoans()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}
```

- [ ] **Step 2: Add bypass button in actions column**

After the approve button (L113), add:
```html
<Button v-if="canBypass && slotProps.data.status === 'submitted'" icon="pi pi-forward" size="small" text rounded severity="warn" @click="openBypass(slotProps.data.id)" v-tooltip.top="'强制跳过'" />
```

- [ ] **Step 3: Add bypass dialog**

Add after the form dialog:
```html
<Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
  <div class="flex flex-col gap-3">
    <p class="text-sm text-stone-600">您正在强制跳过借款审批，此操作将记录到审计日志。</p>
    <label class="form-label">跳过原因（必填）</label>
    <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
  </div>
  <template #footer>
    <Button label="取消" severity="secondary" @click="bypassDialog = false" />
    <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypass" />
  </template>
</Dialog>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/expenses/ExpenseLoanList.vue
git commit -m "feat: add bypass button to ExpenseLoanList"
```

---

### Task 10: Add bypass button to BidExceptionList

**Files:**
- Modify: `frontend/src/views/bids/BidExceptionList.vue`

- [ ] **Step 1: Import bypass API and add logic**

Add to import:
```typescript
import { ..., bypassExceptionEvent } from '@/api/bids'
```

Add in `<script setup>`:
```typescript
const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentExceptionId = ref<number | null>(null)

const openBypassException = (id: number) => { currentExceptionId.value = id; bypassReason.value = ''; bypassDialog.value = true }

const doBypassException = async () => {
  try {
    await bypassExceptionEvent(currentExceptionId.value!, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}
```

- [ ] **Step 2: Add bypass button in actions column**

After the approve button (L243), add:
```html
<Button v-if="canBypass && data.status === 'reviewed'" icon="pi pi-forward" size="small" severity="warn" @click="openBypassException(data.id)" v-tooltip.top="'强制跳过'" />
```

- [ ] **Step 3: Add bypass dialog**

Add after existing dialogs:
```html
<Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
  <div class="flex flex-col gap-3">
    <p class="text-sm text-stone-600">您正在强制跳过例外事项审批，此操作将记录到审计日志。</p>
    <label class="form-label">跳过原因（必填）</label>
    <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
  </div>
  <template #footer>
    <Button label="取消" severity="secondary" @click="bypassDialog = false" />
    <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypassException" />
  </template>
</Dialog>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/bids/BidExceptionList.vue
git commit -m "feat: add bypass button to BidExceptionList"
```

---

### Task 11: Add bypass button to TenderProjectList

**Files:**
- Modify: `frontend/src/views/bids/TenderProjectList.vue`

- [ ] **Step 1: Find `isPrivileged` or add role check, import bypass API**

Check if `isPrivileged` already exists in this file. If not, add:
```typescript
import { ..., bypassTenderProject } from '@/api/bids'

const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentProjectId = ref<number | null>(null)

const openBypassProject = (id: number) => { currentProjectId.value = id; bypassReason.value = ''; bypassDialog.value = true }

const doBypassProject = async () => {
  try {
    await bypassTenderProject(currentProjectId.value!, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}
```

- [ ] **Step 2: Add bypass button in actions column where approve button exists**

```html
<Button v-if="canBypass && data.status === 'draft'" icon="pi pi-forward" size="small" severity="warn" @click="openBypassProject(data.id)" v-tooltip.top="'强制跳过'" />
```

- [ ] **Step 3: Add bypass dialog**

Same pattern as Task 10.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/bids/TenderProjectList.vue
git commit -m "feat: add bypass button to TenderProjectList"
```

---

### Task 12: Run backend test

- [ ] **Step 1: Start backend**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000 &
sleep 2
```

- [ ] **Step 2: Test report bypass endpoint**

```bash
curl -s -X POST http://localhost:8000/api/expenses/reports/1/bypass \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(python3 -c "import sqlite3; c=sqlite3.connect('backend/app.db'); print(c.execute('SELECT id FROM users WHERE role=\"super_admin\" LIMIT 1').fetchone()[0])")" \
  -d '{"reason":"测试强制跳过"}'
```

Verify: Returns 200 with updated report. If no report exists, expect 404 (OK).

- [ ] **Step 3: Test loan bypass endpoint**

```bash
curl -s -X POST http://localhost:8000/api/expenses/loans/1/bypass \
  -H "Content-Type: application/json" \
  -d '{"reason":"测试强制跳过"}'
```

- [ ] **Step 4: Stop backend**

```bash
pkill -f "uvicorn app.main"
```

- [ ] **Step 5: Commit (if any fixes)**

```bash
git add -A && git commit -m "fix: test and finalize bypass endpoints"
```
