import{C as e,H as t,K as n,O as r,R as i,T as a,dt as o,g as s,h as c,m as l,mt as u,s as d,u as f,x as p}from"./runtime-core.esm-bundler-DVgfZ4Qj.js";import{s as m,t as h}from"./button-CiTpQ2Aq.js";import{Kn as g,Ma as _,Pi as v,bt as y,ka as b,mi as x,v as S}from"./index-DHOdsQMJ.js";import{n as C}from"./baseinput-x13cuk6s.js";import{t as w}from"./inputtext-BM8yyzXI.js";import{t as T}from"./dropdown-DdGrLFTS.js";import{t as E}from"./dialog-iryXBYSu.js";import{n as D,t as O}from"./column-Cg-5Q8o7.js";var k=_.extend({name:`toggleswitch`,style:`
    .p-toggleswitch {
        display: inline-block;
        width: dt('toggleswitch.width');
        height: dt('toggleswitch.height');
    }

    .p-toggleswitch-input {
        cursor: pointer;
        appearance: none;
        position: absolute;
        top: 0;
        inset-inline-start: 0;
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
        opacity: 0;
        z-index: 1;
        outline: 0 none;
        border-radius: dt('toggleswitch.border.radius');
    }

    .p-toggleswitch-slider {
        cursor: pointer;
        width: 100%;
        height: 100%;
        border-width: dt('toggleswitch.border.width');
        border-style: solid;
        border-color: dt('toggleswitch.border.color');
        background: dt('toggleswitch.background');
        transition:
            background dt('toggleswitch.transition.duration'),
            color dt('toggleswitch.transition.duration'),
            border-color dt('toggleswitch.transition.duration'),
            outline-color dt('toggleswitch.transition.duration'),
            box-shadow dt('toggleswitch.transition.duration');
        border-radius: dt('toggleswitch.border.radius');
        outline-color: transparent;
        box-shadow: dt('toggleswitch.shadow');
    }

    .p-toggleswitch-handle {
        position: absolute;
        top: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        background: dt('toggleswitch.handle.background');
        color: dt('toggleswitch.handle.color');
        width: dt('toggleswitch.handle.size');
        height: dt('toggleswitch.handle.size');
        inset-inline-start: dt('toggleswitch.gap');
        margin-block-start: calc(-1 * calc(dt('toggleswitch.handle.size') / 2));
        border-radius: dt('toggleswitch.handle.border.radius');
        transition:
            background dt('toggleswitch.transition.duration'),
            color dt('toggleswitch.transition.duration'),
            inset-inline-start dt('toggleswitch.slide.duration'),
            box-shadow dt('toggleswitch.slide.duration');
    }

    .p-toggleswitch.p-toggleswitch-checked .p-toggleswitch-slider {
        background: dt('toggleswitch.checked.background');
        border-color: dt('toggleswitch.checked.border.color');
    }

    .p-toggleswitch.p-toggleswitch-checked .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.checked.background');
        color: dt('toggleswitch.handle.checked.color');
        inset-inline-start: calc(dt('toggleswitch.width') - calc(dt('toggleswitch.handle.size') + dt('toggleswitch.gap')));
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover) .p-toggleswitch-slider {
        background: dt('toggleswitch.hover.background');
        border-color: dt('toggleswitch.hover.border.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover) .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.hover.background');
        color: dt('toggleswitch.handle.hover.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover).p-toggleswitch-checked .p-toggleswitch-slider {
        background: dt('toggleswitch.checked.hover.background');
        border-color: dt('toggleswitch.checked.hover.border.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:hover).p-toggleswitch-checked .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.checked.hover.background');
        color: dt('toggleswitch.handle.checked.hover.color');
    }

    .p-toggleswitch:not(.p-disabled):has(.p-toggleswitch-input:focus-visible) .p-toggleswitch-slider {
        box-shadow: dt('toggleswitch.focus.ring.shadow');
        outline: dt('toggleswitch.focus.ring.width') dt('toggleswitch.focus.ring.style') dt('toggleswitch.focus.ring.color');
        outline-offset: dt('toggleswitch.focus.ring.offset');
    }

    .p-toggleswitch.p-invalid > .p-toggleswitch-slider {
        border-color: dt('toggleswitch.invalid.border.color');
    }

    .p-toggleswitch.p-disabled {
        opacity: 1;
    }

    .p-toggleswitch.p-disabled .p-toggleswitch-slider {
        background: dt('toggleswitch.disabled.background');
    }

    .p-toggleswitch.p-disabled .p-toggleswitch-handle {
        background: dt('toggleswitch.handle.disabled.background');
    }
`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-toggleswitch p-component`,{"p-toggleswitch-checked":t.checked,"p-disabled":n.disabled,"p-invalid":t.$invalid}]},input:`p-toggleswitch-input`,slider:`p-toggleswitch-slider`,handle:`p-toggleswitch-handle`},inlineStyles:{root:{position:`relative`}}}),A={name:`ToggleSwitch`,extends:{name:`BaseToggleSwitch`,extends:C,props:{trueValue:{type:null,default:!0},falseValue:{type:null,default:!1},readonly:{type:Boolean,default:!1},tabindex:{type:Number,default:null},inputId:{type:String,default:null},inputClass:{type:[String,Object],default:null},inputStyle:{type:Object,default:null},ariaLabelledby:{type:String,default:null},ariaLabel:{type:String,default:null}},style:k,provide:function(){return{$pcToggleSwitch:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`change`,`focus`,`blur`],methods:{getPTOptions:function(e){return(e===`root`?this.ptmi:this.ptm)(e,{context:{checked:this.checked,disabled:this.disabled}})},onChange:function(e){if(!this.disabled&&!this.readonly){var t=this.checked?this.falseValue:this.trueValue;this.writeValue(t,e),this.$emit(`change`,e)}},onFocus:function(e){this.$emit(`focus`,e)},onBlur:function(e){var t,n;this.$emit(`blur`,e),(t=(n=this.formField).onBlur)==null||t.call(n,e)}},computed:{checked:function(){return this.d_value===this.trueValue},dataP:function(){return m({checked:this.checked,disabled:this.disabled,invalid:this.$invalid})}}},j=[`data-p-checked`,`data-p-disabled`,`data-p`],M=[`id`,`checked`,`tabindex`,`disabled`,`readonly`,`aria-checked`,`aria-labelledby`,`aria-label`,`aria-invalid`],N=[`data-p`],P=[`data-p`];function F(e,t,n,i,o,s){return a(),f(`div`,p({class:e.cx(`root`),style:e.sx(`root`)},s.getPTOptions(`root`),{"data-p-checked":s.checked,"data-p-disabled":e.disabled,"data-p":s.dataP}),[d(`input`,p({id:e.inputId,type:`checkbox`,role:`switch`,class:[e.cx(`input`),e.inputClass],style:e.inputStyle,checked:s.checked,tabindex:e.tabindex,disabled:e.disabled,readonly:e.readonly,"aria-checked":s.checked,"aria-labelledby":e.ariaLabelledby,"aria-label":e.ariaLabel,"aria-invalid":e.invalid||void 0,onFocus:t[0]||=function(){return s.onFocus&&s.onFocus.apply(s,arguments)},onBlur:t[1]||=function(){return s.onBlur&&s.onBlur.apply(s,arguments)},onChange:t[2]||=function(){return s.onChange&&s.onChange.apply(s,arguments)}},s.getPTOptions(`input`)),null,16,M),d(`div`,p({class:e.cx(`slider`)},s.getPTOptions(`slider`),{"data-p":s.dataP}),[d(`div`,p({class:e.cx(`handle`)},s.getPTOptions(`handle`),{"data-p":s.dataP}),[r(e.$slots,`handle`,{checked:s.checked})],16,P)],16,N)],16,j)}A.render=F;var I={class:`flex items-center justify-between mb-4`},L={class:`flex gap-2`},R={class:`bg-white rounded-sm border border-zinc-200 shadow-sm`},z={class:`text-xs bg-zinc-100 px-1 rounded`},B={class:`text-xs bg-zinc-100 px-1 rounded`},V={class:`flex flex-col gap-3 pt-2`},H={class:`flex gap-3`},U={class:`flex-1`},W={class:`flex items-center gap-2`},G=s({__name:`CashFlowItems`,setup(r){let s=b(),p=t([]),m=t(!1),_=t(!1),C=t(!1),k=t(null),j=()=>({code:``,name:``,category_code:``,direction:`inflow`,debit_accounts:``,credit_accounts:``,is_active:!0}),M=t(j()),N=[{label:`销售商品收到现金`,value:`op_sales`},{label:`税费返还`,value:`op_refund`},{label:`其他经营流入`,value:`op_other_in`},{label:`购买商品支付现金`,value:`op_goods`},{label:`支付职工`,value:`op_staff`},{label:`支付税费`,value:`op_tax`},{label:`其他经营流出`,value:`op_other_out`},{label:`收回投资`,value:`inv_recover`},{label:`投资收益`,value:`inv_income`},{label:`处置资产收回`,value:`inv_assets`},{label:`购建固定资产支付`,value:`inv_build`},{label:`投资支付`,value:`inv_pay`},{label:`吸收投资`,value:`fin_invest`},{label:`取得借款`,value:`fin_borrow`},{label:`偿还债务`,value:`fin_repay`},{label:`分配股利`,value:`fin_dividend`}],P=[{label:`流入 (inflow)`,value:`inflow`},{label:`流出 (outflow)`,value:`outflow`}];function F(e){let t=N.find(t=>t.value===e);return t?t.label:e}async function G(){m.value=!0;try{let e=await g(Number(JSON.parse(localStorage.getItem(`user`)||`{}`).company_id||1));p.value=Array.isArray(e.data)?e.data:[]}catch(e){s.add({severity:`error`,summary:`加载失败`,detail:String(e),life:4e3})}finally{m.value=!1}}function K(){C.value=!1,k.value=null,M.value=j(),_.value=!0}function q(e){C.value=!0,k.value=e.id,M.value={code:e.code,name:e.name,category_code:e.category_code||``,direction:e.direction||`inflow`,debit_accounts:e.debit_accounts||``,credit_accounts:e.credit_accounts||``,is_active:e.is_active},_.value=!0}async function J(){try{let e=Number(JSON.parse(localStorage.getItem(`user`)||`{}`).company_id||1);C.value&&k.value?(await v(k.value,M.value),s.add({severity:`success`,summary:`已更新`,life:2e3})):(await S({...M.value,company_id:e}),s.add({severity:`success`,summary:`已创建`,life:2e3})),_.value=!1,await G()}catch(e){s.add({severity:`error`,summary:`保存失败`,detail:e?.response?.data?.detail||String(e),life:4e3})}}async function Y(e){if(confirm(`确认删除 "${e.name}"？`))try{await y(e.id),s.add({severity:`success`,summary:`已删除`,life:2e3}),await G()}catch(e){s.add({severity:`error`,summary:`删除失败`,detail:String(e),life:4e3})}}async function X(){if(confirm(`将用国标预设项目重置当前公司的现金流量映射，确认？`))try{await x(Number(JSON.parse(localStorage.getItem(`user`)||`{}`).company_id||1)),s.add({severity:`success`,summary:`已补齐国标预设`,life:2e3}),await G()}catch(e){s.add({severity:`error`,summary:`操作失败`,detail:String(e),life:4e3})}}return e(()=>G()),(e,t)=>(a(),f(`div`,null,[d(`div`,I,[t[9]||=d(`h2`,{class:`text-lg font-semibold text-zinc-800`},`现金流量表项目映射`,-1),d(`div`,L,[c(n(h),{label:`补齐国标预设`,icon:`pi pi-refresh`,severity:`secondary`,size:`small`,onClick:X}),c(n(h),{label:`新增项目`,icon:`pi pi-plus`,size:`small`,onClick:K})])]),d(`div`,R,[c(n(D),{value:p.value,loading:m.value,stripedRows:``,size:`small`,tableStyle:`min-width: auto`},{default:i(()=>[c(n(O),{field:`code`,header:`编码`,style:{width:`80px`}}),c(n(O),{field:`name`,header:`项目名称`,style:{width:`260px`}}),c(n(O),{header:`报表位置`,style:{width:`150px`}},{body:i(({data:e})=>[l(u(F(e.category_code)),1)]),_:1}),c(n(O),{header:`方向`,style:{width:`70px`}},{body:i(({data:e})=>[d(`span`,{class:o(e.direction===`inflow`?`text-green-600`:`text-red-600`)},u(e.direction===`inflow`?`流入`:`流出`),3)]),_:1}),c(n(O),{field:`debit_accounts`,header:`借方对方科目`,style:{width:`200px`}},{body:i(({data:e})=>[d(`code`,z,u(e.debit_accounts||`-`),1)]),_:1}),c(n(O),{field:`credit_accounts`,header:`贷方对方科目`,style:{width:`200px`}},{body:i(({data:e})=>[d(`code`,B,u(e.credit_accounts||`-`),1)]),_:1}),c(n(O),{header:`启用`,style:{width:`60px`}},{body:i(({data:e})=>[d(`i`,{class:o(e.is_active?`pi pi-check text-green-500`:`pi pi-times text-red-400`)},null,2)]),_:1}),c(n(O),{header:`操作`,style:{width:`120px`}},{body:i(({data:e})=>[c(n(h),{icon:`pi pi-pencil`,severity:`secondary`,text:``,size:`small`,onClick:t=>q(e)},null,8,[`onClick`]),c(n(h),{icon:`pi pi-trash`,severity:`danger`,text:``,size:`small`,onClick:t=>Y(e)},null,8,[`onClick`])]),_:1})]),_:1},8,[`value`,`loading`])]),c(n(E),{visible:_.value,"onUpdate:visible":t[8]||=e=>_.value=e,header:C.value?`编辑现金流量项目`:`新增现金流量项目`,modal:!0,class:`w-[520px]`},{footer:i(()=>[c(n(h),{label:`取消`,severity:`secondary`,onClick:t[7]||=e=>_.value=!1}),c(n(h),{label:`保存`,onClick:J})]),default:i(()=>[d(`div`,V,[d(`div`,H,[d(`div`,U,[t[10]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},`编码`,-1),c(n(w),{modelValue:M.value.code,"onUpdate:modelValue":t[0]||=e=>M.value.code=e,class:`w-full`,disabled:C.value},null,8,[`modelValue`,`disabled`])]),d(`div`,null,[t[11]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},`方向`,-1),c(n(T),{modelValue:M.value.direction,"onUpdate:modelValue":t[1]||=e=>M.value.direction=e,options:P,optionLabel:`label`,optionValue:`value`,class:`w-32`},null,8,[`modelValue`])])]),d(`div`,null,[t[12]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},`项目名称`,-1),c(n(w),{modelValue:M.value.name,"onUpdate:modelValue":t[2]||=e=>M.value.name=e,class:`w-full`},null,8,[`modelValue`])]),d(`div`,null,[t[13]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},`映射到报表行`,-1),c(n(T),{modelValue:M.value.category_code,"onUpdate:modelValue":t[3]||=e=>M.value.category_code=e,options:N,optionLabel:`label`,optionValue:`value`,class:`w-full`,showClear:``,placeholder:`选择报表行...`},null,8,[`modelValue`])]),d(`div`,null,[t[14]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},[l(` 借方对方科目 `),d(`span`,{class:`text-zinc-400`},`（现金流出时，对方借方的科目范围）`)],-1),c(n(w),{modelValue:M.value.debit_accounts,"onUpdate:modelValue":t[4]||=e=>M.value.debit_accounts=e,class:`w-full`,placeholder:`如: 2211,2221,6602`},null,8,[`modelValue`])]),d(`div`,null,[t[15]||=d(`label`,{class:`block text-sm text-zinc-600 mb-1`},[l(` 贷方对方科目 `),d(`span`,{class:`text-zinc-400`},`（现金流入时，对方贷方的科目范围）`)],-1),c(n(w),{modelValue:M.value.credit_accounts,"onUpdate:modelValue":t[5]||=e=>M.value.credit_accounts=e,class:`w-full`,placeholder:`如: 1122,6001,2241`},null,8,[`modelValue`])]),d(`div`,W,[c(n(A),{modelValue:M.value.is_active,"onUpdate:modelValue":t[6]||=e=>M.value.is_active=e},null,8,[`modelValue`]),t[16]||=d(`span`,{class:`text-sm text-zinc-600`},`启用该项目`,-1)])])]),_:1},8,[`visible`,`header`])]))}});export{G as default};