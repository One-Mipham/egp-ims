import{A as e,D as t,H as n,K as r,O as i,R as a,T as o,c as s,dt as c,g as l,h as u,j as d,k as f,l as p,m,mt as h,r as g,s as _,u as v,x as y,z as b}from"./runtime-core.esm-bundler-DVgfZ4Qj.js";import{n as x,s as S,t as C}from"./button-BJX9Eopd.js";import{Da as w,Ko as T,On as E,Vo as D,Ya as O,co as k,wa as A,yo as j}from"./index-Dpkr7PMM.js";import{t as M}from"./basecomponent-Pv2neNRv.js";import{n as N}from"./overlayeventbus-CODyOAXx.js";import{t as P}from"./inputtext-DIi2HRyd.js";import{t as ee}from"./dropdown-zYOWyZME.js";import{t as F}from"./checkbox-C6ZOGULg.js";import{n as I,t as L}from"./column-7wLve5w2.js";import{t as R}from"./chevronright-BGkWnQdY.js";import{t as z}from"./chevronup-Ck6v16TK.js";var B=w.extend({name:`accordioncontent`,classes:{root:`p-accordioncontent`,contentWrapper:`p-accordioncontent-wrapper`,content:`p-accordioncontent-content`}}),V={name:`AccordionContent`,extends:{name:`BaseAccordionContent`,extends:M,props:{as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:B,provide:function(){return{$pcAccordionContent:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],computed:{id:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},ariaLabelledby:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},attrs:function(){return y(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{id:this.id,role:`region`,"aria-labelledby":this.ariaLabelledby,"data-pc-name":`accordioncontent`,"data-p-active":this.$pcAccordionPanel.active}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}}}};function H(e,t,n,r,l,u){return e.asChild?i(e.$slots,`default`,{key:1,class:c(e.cx(`root`)),active:u.$pcAccordionPanel.active,a11yAttrs:u.a11yAttrs}):(o(),s(D,y({key:0,name:`p-collapsible`},e.ptm(`transition`,u.ptParams)),{default:a(function(){return[!u.$pcAccordion.lazy||u.$pcAccordionPanel.active?b((o(),s(d(e.as),y({key:0,class:e.cx(`root`)},u.attrs),{default:a(function(){return[_(`div`,y({class:e.cx(`contentWrapper`)},e.ptm(`contentWrapper`,u.ptParams)),[_(`div`,y({class:e.cx(`content`)},e.ptm(`content`,u.ptParams)),[i(e.$slots,`default`)],16)],16)]}),_:3},16,[`class`])),[[T,u.$pcAccordion.lazy?!0:u.$pcAccordionPanel.active]]):p(``,!0)]}),_:3},16))}V.render=H;var U=w.extend({name:`accordionheader`,classes:{root:`p-accordionheader`,toggleicon:`p-accordionheader-toggle-icon`}}),W={name:`AccordionHeader`,extends:{name:`BaseAccordionHeader`,extends:M,props:{as:{type:[String,Object],default:`BUTTON`},asChild:{type:Boolean,default:!1}},style:U,provide:function(){return{$pcAccordionHeader:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],methods:{onFocus:function(){this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onClick:function(){!this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onKeydown:function(e){switch(e.code){case`ArrowDown`:this.onArrowDownKey(e);break;case`ArrowUp`:this.onArrowUpKey(e);break;case`Home`:this.onHomeKey(e);break;case`End`:this.onEndKey(e);break;case`Enter`:case`NumpadEnter`:case`Space`:this.onEnterKey(e);break}},onArrowDownKey:function(e){var t=this.findNextPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onHomeKey(e),e.preventDefault()},onArrowUpKey:function(e){var t=this.findPrevPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onEndKey(e),e.preventDefault()},onHomeKey:function(e){var t=this.findFirstPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEndKey:function(e){var t=this.findLastPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEnterKey:function(e){this.changeActiveValue(),e.preventDefault()},findPanel:function(e){return e?.closest(`[data-pc-name="accordionpanel"]`)},findHeader:function(e){return j(e,`[data-pc-name="accordionheader"]`)},findNextPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.nextElementSibling;return t?O(t,`data-p-disabled`)?this.findNextPanel(t):this.findHeader(t):null},findPrevPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.previousElementSibling;return t?O(t,`data-p-disabled`)?this.findPrevPanel(t):this.findHeader(t):null},findFirstPanel:function(){return this.findNextPanel(this.$pcAccordion.$el.firstElementChild,!0)},findLastPanel:function(){return this.findPrevPanel(this.$pcAccordion.$el.lastElementChild,!0)},changeActiveValue:function(){this.$pcAccordion.updateValue(this.$pcAccordionPanel.value)},changeFocusedPanel:function(e,t){k(this.findHeader(t))}},computed:{id:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},ariaControls:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},attrs:function(){return y(this.asAttrs,this.a11yAttrs,this.ptmi(`root`,this.ptParams))},asAttrs:function(){return this.as===`BUTTON`?{type:`button`,disabled:this.$pcAccordionPanel.disabled}:void 0},a11yAttrs:function(){return{id:this.id,tabindex:this.$pcAccordion.tabindex,"aria-expanded":this.$pcAccordionPanel.active,"aria-controls":this.ariaControls,"data-pc-name":`accordionheader`,"data-p-disabled":this.$pcAccordionPanel.disabled,"data-p-active":this.$pcAccordionPanel.active,onFocus:this.onFocus,onKeydown:this.onKeydown}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}},dataP:function(){return S({active:this.$pcAccordionPanel.active})}},components:{ChevronUpIcon:z,ChevronDownIcon:N},directives:{ripple:x}};function G(t,n,r,l,u,f){var p=e(`ripple`);return t.asChild?i(t.$slots,`default`,{key:1,class:c(t.cx(`root`)),active:f.$pcAccordionPanel.active,a11yAttrs:f.a11yAttrs,onClick:f.onClick}):b((o(),s(d(t.as),y({key:0,"data-p":f.dataP,class:t.cx(`root`),onClick:f.onClick},f.attrs),{default:a(function(){return[i(t.$slots,`default`,{active:f.$pcAccordionPanel.active}),i(t.$slots,`toggleicon`,{active:f.$pcAccordionPanel.active,class:c(t.cx(`toggleicon`))},function(){return[f.$pcAccordionPanel.active?(o(),s(d(f.$pcAccordion.$slots.collapseicon?f.$pcAccordion.$slots.collapseicon:f.$pcAccordion.collapseIcon?`span`:`ChevronUpIcon`),y({key:0,class:[f.$pcAccordion.collapseIcon,t.cx(`toggleicon`)],"aria-hidden":`true`},t.ptm(`toggleicon`,f.ptParams)),null,16,[`class`])):(o(),s(d(f.$pcAccordion.$slots.expandicon?f.$pcAccordion.$slots.expandicon:f.$pcAccordion.expandIcon?`span`:`ChevronDownIcon`),y({key:1,class:[f.$pcAccordion.expandIcon,t.cx(`toggleicon`)],"aria-hidden":`true`},t.ptm(`toggleicon`,f.ptParams)),null,16,[`class`]))]})]}),_:3},16,[`data-p`,`class`,`onClick`])),[[p]])}W.render=G;var K=w.extend({name:`accordionpanel`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-accordionpanel`,{"p-accordionpanel-active":t.active,"p-disabled":n.disabled}]}}}),q={name:`AccordionPanel`,extends:{name:`BaseAccordionPanel`,extends:M,props:{value:{type:[String,Number],default:void 0},disabled:{type:Boolean,default:!1},as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:K,provide:function(){return{$pcAccordionPanel:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`],computed:{active:function(){return this.$pcAccordion.isItemActive(this.value)},attrs:function(){return y(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{"data-pc-name":`accordionpanel`,"data-p-disabled":this.disabled,"data-p-active":this.active}},ptParams:function(){return{context:{active:this.active}}}}};function J(e,t,n,r,l,u){return e.asChild?i(e.$slots,`default`,{key:1,class:c(e.cx(`root`)),active:u.active,a11yAttrs:u.a11yAttrs}):(o(),s(d(e.as),y({key:0,class:e.cx(`root`)},u.attrs),{default:a(function(){return[i(e.$slots,`default`)]}),_:3},16,[`class`]))}q.render=J;var Y=w.extend({name:`accordion`,style:`
    .p-accordionpanel {
        display: flex;
        flex-direction: column;
        border-style: solid;
        border-width: dt('accordion.panel.border.width');
        border-color: dt('accordion.panel.border.color');
    }

    .p-accordionheader {
        all: unset;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: dt('accordion.header.padding');
        color: dt('accordion.header.color');
        background: dt('accordion.header.background');
        border-style: solid;
        border-width: dt('accordion.header.border.width');
        border-color: dt('accordion.header.border.color');
        font-weight: dt('accordion.header.font.weight');
        border-radius: dt('accordion.header.border.radius');
        transition:
            background dt('accordion.transition.duration'),
            color dt('accordion.transition.duration'),
            outline-color dt('accordion.transition.duration'),
            box-shadow dt('accordion.transition.duration');
        outline-color: transparent;
    }

    .p-accordionpanel:first-child > .p-accordionheader {
        border-width: dt('accordion.header.first.border.width');
        border-start-start-radius: dt('accordion.header.first.top.border.radius');
        border-start-end-radius: dt('accordion.header.first.top.border.radius');
    }

    .p-accordionpanel:last-child > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.bottom.border.radius');
    }

    .p-accordionpanel:last-child.p-accordionpanel-active > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.active.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.active.bottom.border.radius');
    }

    .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.color');
    }

    .p-accordionpanel:not(.p-disabled) .p-accordionheader:focus-visible {
        box-shadow: dt('accordion.header.focus.ring.shadow');
        outline: dt('accordion.header.focus.ring.width') dt('accordion.header.focus.ring.style') dt('accordion.header.focus.ring.color');
        outline-offset: dt('accordion.header.focus.ring.offset');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) > .p-accordionheader:hover {
        background: dt('accordion.header.hover.background');
        color: dt('accordion.header.hover.color');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader {
        background: dt('accordion.header.active.background');
        color: dt('accordion.header.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover {
        background: dt('accordion.header.active.hover.background');
        color: dt('accordion.header.active.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.hover.color');
    }

    .p-accordioncontent {
        display: grid;
        grid-template-rows: 1fr;
    }

    .p-accordioncontent-wrapper {
        min-height: 0;
    }

    .p-accordioncontent-content {
        border-style: solid;
        border-width: dt('accordion.content.border.width');
        border-color: dt('accordion.content.border.color');
        background-color: dt('accordion.content.background');
        color: dt('accordion.content.color');
        padding: dt('accordion.content.padding');
    }
`,classes:{root:`p-accordion p-component`}}),X={name:`Accordion`,extends:{name:`BaseAccordion`,extends:M,props:{value:{type:[String,Number,Array],default:void 0},multiple:{type:Boolean,default:!1},lazy:{type:Boolean,default:!1},tabindex:{type:Number,default:0},selectOnFocus:{type:Boolean,default:!1},expandIcon:{type:String,default:void 0},collapseIcon:{type:String,default:void 0},activeIndex:{type:[Number,Array],default:null}},style:Y,provide:function(){return{$pcAccordion:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`update:value`,`update:activeIndex`,`tab-open`,`tab-close`,`tab-click`],data:function(){return{d_value:this.value}},watch:{value:function(e){this.d_value=e},activeIndex:{immediate:!0,handler:function(e){this.hasAccordionTab&&(this.d_value=this.multiple?e?.map(String):e?.toString())}}},methods:{isItemActive:function(e){return this.multiple?this.d_value?.includes(e):this.d_value===e},updateValue:function(e){var t=this.isItemActive(e);this.multiple?t?this.d_value=this.d_value.filter(function(t){return t!==e}):this.d_value?this.d_value.push(e):this.d_value=[e]:this.d_value=t?null:e,this.$emit(`update:value`,this.d_value),this.$emit(`update:activeIndex`,this.multiple?this.d_value?.map(Number):Number(this.d_value)),this.$emit(t?`tab-close`:`tab-open`,{originalEvent:void 0,index:Number(e)})},isAccordionTab:function(e){return e.type.name===`AccordionTab`},getTabProp:function(e,t){return e.props?e.props[t]:void 0},getKey:function(e,t){return this.getTabProp(e,`header`)||t},getHeaderPT:function(e,t){var n=this;return{root:y({onClick:function(e){return n.onTabClick(e,t)}},this.getTabProp(e,`headerProps`),this.getTabPT(e,`header`,t)),toggleicon:y(this.getTabProp(e,`headeractionprops`),this.getTabPT(e,`headeraction`,t))}},getContentPT:function(e,t){return{root:y(this.getTabProp(e,`contentProps`),this.getTabPT(e,`toggleablecontent`,t)),transition:this.getTabPT(e,`transition`,t),content:this.getTabPT(e,`content`,t)}},getTabPT:function(e,t,n){var r=this.tabs.length,i={props:e.props||{},parent:{instance:this,props:this.$props,state:this.$data},context:{index:n,count:r,first:n===0,last:n===r-1,active:this.isItemActive(`${n}`)}};return y(this.ptm(`accordiontab.${t}`,i),this.ptmo(this.getTabProp(e,`pt`),t,i))},onTabClick:function(e,t){this.$emit(`tab-click`,{originalEvent:e,index:t})}},computed:{tabs:function(){var e=this;return this.$slots.default().reduce(function(t,n){return e.isAccordionTab(n)?t.push(n):n.children&&n.children instanceof Array&&n.children.forEach(function(n){e.isAccordionTab(n)&&t.push(n)}),t},[])},hasAccordionTab:function(){return this.tabs.length}},components:{AccordionPanel:q,AccordionHeader:W,AccordionContent:V,ChevronUpIcon:z,ChevronRightIcon:R}};function Z(e,n,r,l,m,_){var b=f(`AccordionHeader`),x=f(`AccordionContent`),S=f(`AccordionPanel`);return o(),v(`div`,y({class:e.cx(`root`)},e.ptmi(`root`)),[_.hasAccordionTab?(o(!0),v(g,{key:0},t(_.tabs,function(t,n){return o(),s(S,{key:_.getKey(t,n),value:`${n}`,pt:{root:_.getTabPT(t,`root`,n)},disabled:_.getTabProp(t,`disabled`)},{default:a(function(){return[u(b,{class:c(_.getTabProp(t,`headerClass`)),pt:_.getHeaderPT(t,n)},{toggleicon:a(function(r){return[r.active?(o(),s(d(e.$slots.collapseicon?e.$slots.collapseicon:e.collapseIcon?`span`:`ChevronDownIcon`),y({key:0,class:[e.collapseIcon,r.class],"aria-hidden":`true`},{ref_for:!0},_.getTabPT(t,`headericon`,n)),null,16,[`class`])):(o(),s(d(e.$slots.expandicon?e.$slots.expandicon:e.expandIcon?`span`:`ChevronUpIcon`),y({key:1,class:[e.expandIcon,r.class],"aria-hidden":`true`},{ref_for:!0},_.getTabPT(t,`headericon`,n)),null,16,[`class`]))]}),default:a(function(){return[t.children&&t.children.headericon?(o(),s(d(t.children.headericon),{key:0,isTabActive:_.isItemActive(`${n}`),active:_.isItemActive(`${n}`),index:n},null,8,[`isTabActive`,`active`,`index`])):p(``,!0),t.props&&t.props.header?(o(),v(`span`,y({key:1,ref_for:!0},_.getTabPT(t,`headertitle`,n)),h(t.props.header),17)):p(``,!0),t.children&&t.children.header?(o(),s(d(t.children.header),{key:2})):p(``,!0)]}),_:2},1032,[`class`,`pt`]),u(x,{pt:_.getContentPT(t,n)},{default:a(function(){return[(o(),s(d(t)))]}),_:2},1032,[`pt`])]}),_:2},1032,[`value`,`pt`,`disabled`])}),128)):i(e.$slots,`default`,{key:1})],16)}X.render=Z;var Q=w.extend({name:`accordiontab`}),$={name:`AccordionTab`,extends:{name:`BaseAccordionTab`,extends:M,props:{header:null,headerStyle:null,headerClass:null,headerProps:null,headerActionProps:null,contentStyle:null,contentClass:null,contentProps:null,disabled:Boolean},style:Q,provide:function(){return{$pcAccordionTab:this,$parentInstance:this}}},inheritAttrs:!1,mounted:function(){console.warn(`Deprecated since v4. Use the new structure of Accordion instead.`)}};function te(e,t,n,r,a,o){return i(e.$slots,`default`)}$.render=te;var ne={class:`p-4`},re={class:`flex gap-3 items-end mb-4 flex-wrap`},ie={class:`flex items-center gap-2`},ae={class:`flex justify-between w-full pr-4`},oe={class:`text-sm`},se={key:1,class:`text-center text-gray-400 py-8`},ce=l({__name:`SubjectLedger`,setup(e){let i=A(),c=Number(localStorage.getItem(`company_id`)||`1`),l=new Date,d=`${l.getFullYear()}-${String(l.getMonth()+1).padStart(2,`0`)}`,f=n({account_code:``,level:null,start_period:d,end_period:d,include_zero:!1}),y=n([]),b=n(!1),x=n(null);async function S(){try{let{data:e}=await E(c,f.value.start_period,f.value.end_period,{account_code:f.value.account_code||void 0,level:f.value.level||void 0,include_zero:f.value.include_zero});y.value=e,b.value=!0,x.value=0}catch(e){i.add({severity:`error`,summary:`查询失败`,detail:e.response?.data?.detail||``,life:5e3})}}return(e,n)=>(o(),v(`div`,ne,[n[10]||=_(`h2`,{class:`text-xl font-bold mb-4`},`科目账`,-1),_(`div`,re,[_(`div`,null,[n[5]||=_(`label`,{class:`block text-sm mb-1`},`科目代码`,-1),u(r(P),{modelValue:f.value.account_code,"onUpdate:modelValue":n[0]||=e=>f.value.account_code=e,placeholder:`如 1001 或 660`},null,8,[`modelValue`])]),_(`div`,null,[n[6]||=_(`label`,{class:`block text-sm mb-1`},`级别`,-1),u(r(ee),{modelValue:f.value.level,"onUpdate:modelValue":n[1]||=e=>f.value.level=e,options:[null,1,2,3,4],class:`w-24`},{value:a(e=>[m(h(e.value?e.value+`级`:`全部`),1)]),option:a(e=>[m(h(e.option?e.option+`级`:`全部`),1)]),_:1},8,[`modelValue`])]),_(`div`,null,[n[7]||=_(`label`,{class:`block text-sm mb-1`},`起始期间`,-1),u(r(P),{modelValue:f.value.start_period,"onUpdate:modelValue":n[2]||=e=>f.value.start_period=e,placeholder:`yyyy-MM`},null,8,[`modelValue`])]),_(`div`,null,[n[8]||=_(`label`,{class:`block text-sm mb-1`},`截止期间`,-1),u(r(P),{modelValue:f.value.end_period,"onUpdate:modelValue":n[3]||=e=>f.value.end_period=e,placeholder:`yyyy-MM`},null,8,[`modelValue`])]),_(`div`,ie,[u(r(F),{modelValue:f.value.include_zero,"onUpdate:modelValue":n[4]||=e=>f.value.include_zero=e,binary:!0,inputId:`include_zero`},null,8,[`modelValue`]),n[9]||=_(`label`,{for:`include_zero`},`含无发生额`,-1)]),u(r(C),{label:`查询`,icon:`pi pi-search`,onClick:S})]),y.value.length?(o(),s(r(X),{key:0,activeIndex:x.value},{default:a(()=>[(o(!0),v(g,null,t(y.value,(e,t)=>(o(),s(r($),{key:t},{header:a(()=>[_(`div`,ae,[_(`span`,null,[_(`strong`,null,h(e.account_code),1),m(` `+h(e.account_name),1)]),_(`span`,oe,`期初: `+h(e.beginning_balance.toLocaleString())+` | 借: `+h(e.total_debit.toLocaleString())+` | 贷: `+h(e.total_credit.toLocaleString())+` | 期末: `+h(e.ending_balance.toLocaleString()),1)])]),default:a(()=>[u(r(I),{value:e.entries,size:`small`,stripedRows:``},{default:a(()=>[u(r(L),{field:`date`,header:`日期`,style:{width:`7rem`}}),u(r(L),{field:`voucher_no`,header:`凭证号`,style:{width:`7rem`}}),u(r(L),{field:`summary`,header:`摘要`}),u(r(L),{field:`debit`,header:`借方`,style:{width:`8rem`}},{body:a(({data:e})=>[m(h(e.debit?e.debit.toLocaleString():``),1)]),_:1}),u(r(L),{field:`credit`,header:`贷方`,style:{width:`8rem`}},{body:a(({data:e})=>[m(h(e.credit?e.credit.toLocaleString():``),1)]),_:1}),u(r(L),{field:`balance`,header:`余额`,style:{width:`8rem`}},{body:a(({data:e})=>[m(h(e.balance.toLocaleString()),1)]),_:1})]),_:1},8,[`value`])]),_:2},1024))),128))]),_:1},8,[`activeIndex`])):b.value?(o(),v(`div`,se,`无查询结果`)):p(``,!0)]))}});export{ce as default};