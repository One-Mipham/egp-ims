# 审批流程柔性化 — 强制跳过机制

> **日期**: 2026-05-21
> **状态**: 已批准
> **范围**: omc-project1 后端 + 前端

## 目标

确保所有审批环节非强制，super_admin / finance_director 可在任意审批节点一键跳过，防止因审批人缺席导致流程卡死。

## 核心原则

审批链作为**建议路径**而非强制关卡。跳过操作必须：
- 填写跳过原因
- 写入 AuditLog（可追溯）
- 仅 super_admin / finance_director 可执行

## 后端改动

### 1. permissions.py — 新增跳过权限检查

```python
def check_approval_bypass(user) -> str | None:
    if user.role in ("super_admin", "finance_director"):
        return None
    return "仅管理员和财务总监可强制跳过审批"
```

### 2. routers/expenses.py — 费用报销跳过

新增 `POST /reports/{report_id}/bypass`：
- 校验 `check_approval_bypass`
- 将当前审批链节点标记为 `bypassed`
- 推进到下一个审批节点；无下一节点则设状态为 `paid`
- `current_approver_id` 设为下一个审批人
- 写入 AuditLog（action: "bypass_approval"）

新增 `POST /loans/{loan_id}/bypass`：
- 同上模式，跳过当前审批节点

### 3. routers/admin.py — 行政综合跳过

新增 `POST /admin/{target_type}/{target_id}/bypass-step`：
- 校验权限
- 跳过当前审批步骤，推进或完成

### 4. routers/bids.py — 招投标跳过

新增 `POST /tender-projects/{project_id}/bypass`：
- 直接标记项目状态为已审批

新增 `POST /exceptions/{event_id}/bypass`：
- 跳过异常事件审批

### 5. AuditLog 格式

```json
{
  "action": "bypass_approval",
  "target_type": "expense_report|loan|tender_project|exception|admin",
  "target_id": "<id>",
  "bypass_node": "<当前节点名称>",
  "reason": "<用户填写的跳过原因>",
  "operator_id": "<user.id>"
}
```

## 前端改动

在以下组件中，审批操作区添加"强制跳过"按钮：
- `expenses/ExpenseReportList.vue` — 审批行
- `expenses/ExpenseLoanList.vue` — 审批行
- `bids/BidSubmissionList.vue` — 审批行
- `bids/BidExceptionList.vue` — 审批行

按钮行为：
- 仅 `super_admin` / `finance_director` 角色可见
- 点击弹出 Dialog 确认，需填写跳过原因（必填）
- 执行后 toast 提示并刷新列表

## 不涉及

- 凭证审批已有 `post_voucher` 接受 draft 状态直接过账，不需额外跳过
- 不修改审批链构建逻辑
- 不新增审批角色池
- 不新增超时自动升级
