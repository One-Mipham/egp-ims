# 投资管理行业研究

> 日期: 2026-05-08 | 用途: omc-project1 投资管理模块设计参考

## 参考机构

| 机构 | 类型 | 参考要点 |
|------|------|---------|
| Blackstone 黑石 | PE/房地产/信贷 | ILPA 报告模板、Waterfall 分配模型、跨资产风险聚合 |
| Sequoia Capital 红杉 | VC | 项目管道管理、投后增值体系、常青基金结构 |
| SoftBank Vision Fund 软银愿景 | VC/Late-stage | 估值方法论（DCF/可比公司/可比交易）、大规模资金追踪 |
| Carlyle Group 凯雷 | PE/信贷 | 跨资产类别风险管理、投资者报告自动化 |

## 行业标准绩效指标

| 指标 | 公式 | 用途 |
|------|------|------|
| MOIC/TVPI | 总价值 / 投入资本 | 回报倍数 |
| IRR | XIRR(现金流) | 年化收益率 |
| DPI | 累计分配 / 投入资本 | 已实现回报 |
| RVPI | 剩余NAV / 投入资本 | 未实现价值 |
| Cap Rate | NOI / 物业价值 | 房地产估值 |
| Sharpe Ratio | (Rp-Rf)/σp | 风险调整收益 |

## 商业参考系统

| 系统 | 覆盖领域 |
|------|---------|
| BlackRock eFront | 全资产类别 PE/RE/Infra |
| Allvue | 基金会计 + 组合监控 |
| Investran (FIS) | 复杂 Waterfall 会计 |
| Carta | 基金行政管理 + Cap Table |
| Juniper Square | GP-LP 门户 + 投资者报告 |

## 开源参考

| 项目 | 覆盖 |
|------|------|
| Captable Inc. | Cap Table 管理 (TypeScript, AGPL) |
| Ghostfolio | 多资产组合追踪 (NestJS + Angular) |
| Bigcapital | 复式记账 GL 会计 (TypeScript, AGPL) |

## 关键结论

商业成熟的开源基金会计平台尚不存在，核心引擎（Partnership Accounting、Waterfall、Multi-entity Consolidation）仍为商业专有。omc-project1 的投资模块有机会填补中小企业投资会计记录的空白。
