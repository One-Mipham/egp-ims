import{A as e,D as t,O as n,R as r,T as i,c as a,dt as o,j as s,l as c,mt as l,r as u,s as d,u as f,x as p,z as m}from"./runtime-core.esm-bundler-DVgfZ4Qj.js";import{n as h}from"./button-BJX9Eopd.js";import{Da as g,Ko as _,Po as v,Wa as y,Xa as b,Ya as x,co as S,yo as C}from"./index-Dpkr7PMM.js";import{t as w}from"./basecomponent-Pv2neNRv.js";import{t as T}from"./chevronright-BGkWnQdY.js";import{t as E}from"./chevronleft-mg8Tp4bD.js";var D=g.extend({name:`tabview`,style:`
    .p-tabview-tablist-container {
        position: relative;
    }

    .p-tabview-scrollable > .p-tabview-tablist-container {
        overflow: hidden;
    }

    .p-tabview-tablist-scroll-container {
        overflow-x: auto;
        overflow-y: hidden;
        scroll-behavior: smooth;
        scrollbar-width: none;
        overscroll-behavior: contain auto;
    }

    .p-tabview-tablist-scroll-container::-webkit-scrollbar {
        display: none;
    }

    .p-tabview-tablist {
        display: flex;
        margin: 0;
        padding: 0;
        list-style-type: none;
        flex: 1 1 auto;
        background: dt('tabview.tab.list.background');
        border: 1px solid dt('tabview.tab.list.border.color');
        border-width: 0 0 1px 0;
        position: relative;
    }

    .p-tabview-tab-header {
        cursor: pointer;
        user-select: none;
        display: flex;
        align-items: center;
        text-decoration: none;
        position: relative;
        overflow: hidden;
        border-style: solid;
        border-width: 0 0 1px 0;
        border-color: transparent transparent dt('tabview.tab.border.color') transparent;
        color: dt('tabview.tab.color');
        padding: 1rem 1.125rem;
        font-weight: 600;
        border-top-right-radius: dt('border.radius.md');
        border-top-left-radius: dt('border.radius.md');
        transition:
            color dt('tabview.transition.duration'),
            outline-color dt('tabview.transition.duration');
        margin: 0 0 -1px 0;
        outline-color: transparent;
    }

    .p-tabview-tablist-item:not(.p-disabled) .p-tabview-tab-header:focus-visible {
        outline: dt('focus.ring.width') dt('focus.ring.style') dt('focus.ring.color');
        outline-offset: -1px;
    }

    .p-tabview-tablist-item:not(.p-highlight):not(.p-disabled):hover > .p-tabview-tab-header {
        color: dt('tabview.tab.hover.color');
    }

    .p-tabview-tablist-item.p-highlight > .p-tabview-tab-header {
        color: dt('tabview.tab.active.color');
    }

    .p-tabview-tab-title {
        line-height: 1;
        white-space: nowrap;
    }

    .p-tabview-next-button,
    .p-tabview-prev-button {
        position: absolute;
        top: 0;
        margin: 0;
        padding: 0;
        z-index: 2;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: dt('tabview.nav.button.background');
        color: dt('tabview.nav.button.color');
        width: 2.5rem;
        border-radius: 0;
        outline-color: transparent;
        transition:
            color dt('tabview.transition.duration'),
            outline-color dt('tabview.transition.duration');
        box-shadow: dt('tabview.nav.button.shadow');
        border: none;
        cursor: pointer;
        user-select: none;
    }

    .p-tabview-next-button:focus-visible,
    .p-tabview-prev-button:focus-visible {
        outline: dt('focus.ring.width') dt('focus.ring.style') dt('focus.ring.color');
        outline-offset: dt('focus.ring.offset');
    }

    .p-tabview-next-button:hover,
    .p-tabview-prev-button:hover {
        color: dt('tabview.nav.button.hover.color');
    }

    .p-tabview-prev-button {
        left: 0;
    }

    .p-tabview-next-button {
        right: 0;
    }

    .p-tabview-panels {
        background: dt('tabview.tab.panel.background');
        color: dt('tabview.tab.panel.color');
        padding: 0.875rem 1.125rem 1.125rem 1.125rem;
    }

    .p-tabview-ink-bar {
        z-index: 1;
        display: block;
        position: absolute;
        bottom: -1px;
        height: 1px;
        background: dt('tabview.tab.active.border.color');
        transition: 250ms cubic-bezier(0.35, 0, 0.25, 1);
    }
`,classes:{root:function(e){return[`p-tabview p-component`,{"p-tabview-scrollable":e.props.scrollable}]},navContainer:`p-tabview-tablist-container`,prevButton:`p-tabview-prev-button`,navContent:`p-tabview-tablist-scroll-container`,nav:`p-tabview-tablist`,tab:{header:function(e){var t=e.instance,n=e.tab,r=e.index;return[`p-tabview-tablist-item`,t.getTabProp(n,`headerClass`),{"p-tabview-tablist-item-active":t.d_activeIndex===r,"p-disabled":t.getTabProp(n,`disabled`)}]},headerAction:`p-tabview-tab-header`,headerTitle:`p-tabview-tab-title`,content:function(e){var t=e.instance,n=e.tab;return[`p-tabview-panel`,t.getTabProp(n,`contentClass`)]}},inkbar:`p-tabview-ink-bar`,nextButton:`p-tabview-next-button`,panelContainer:`p-tabview-panels`}}),O={name:`TabView`,extends:{name:`BaseTabView`,extends:w,props:{activeIndex:{type:Number,default:0},lazy:{type:Boolean,default:!1},scrollable:{type:Boolean,default:!1},tabindex:{type:Number,default:0},selectOnFocus:{type:Boolean,default:!1},prevButtonProps:{type:null,default:null},nextButtonProps:{type:null,default:null},prevIcon:{type:String,default:void 0},nextIcon:{type:String,default:void 0}},style:D,provide:function(){return{$pcTabs:void 0,$pcTabView:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`update:activeIndex`,`tab-change`,`tab-click`],data:function(){return{d_activeIndex:this.activeIndex,isPrevButtonDisabled:!0,isNextButtonDisabled:!1}},watch:{activeIndex:function(e){this.d_activeIndex=e,this.scrollInView({index:e})}},mounted:function(){console.warn(`Deprecated since v4. Use Tabs component instead.`),this.updateInkBar(),this.scrollable&&this.updateButtonState()},updated:function(){this.updateInkBar(),this.scrollable&&this.updateButtonState()},methods:{isTabPanel:function(e){return e.type.name===`TabPanel`},isTabActive:function(e){return this.d_activeIndex===e},getTabProp:function(e,t){return e.props?e.props[t]:void 0},getKey:function(e,t){return this.getTabProp(e,`header`)||t},getTabHeaderActionId:function(e){return`${this.$id}_${e}_header_action`},getTabContentId:function(e){return`${this.$id}_${e}_content`},getTabPT:function(e,t,n){var r=this.tabs.length,i={props:e.props,parent:{instance:this,props:this.$props,state:this.$data},context:{index:n,count:r,first:n===0,last:n===r-1,active:this.isTabActive(n)}};return p(this.ptm(`tabpanel.${t}`,{tabpanel:i}),this.ptm(`tabpanel.${t}`,i),this.ptmo(this.getTabProp(e,`pt`),t,i))},onScroll:function(e){this.scrollable&&this.updateButtonState(),e.preventDefault()},onPrevButtonClick:function(){var e=this.$refs.content,t=b(e),n=e.scrollLeft-t;e.scrollLeft=n<=0?0:n},onNextButtonClick:function(){var e=this.$refs.content,t=b(e)-this.getVisibleButtonWidths(),n=e.scrollLeft+t,r=e.scrollWidth-t;e.scrollLeft=n>=r?r:n},onTabClick:function(e,t,n){this.changeActiveIndex(e,t,n),this.$emit(`tab-click`,{originalEvent:e,index:n})},onTabKeyDown:function(e,t,n){switch(e.code){case`ArrowLeft`:this.onTabArrowLeftKey(e);break;case`ArrowRight`:this.onTabArrowRightKey(e);break;case`Home`:this.onTabHomeKey(e);break;case`End`:this.onTabEndKey(e);break;case`PageDown`:this.onPageDownKey(e);break;case`PageUp`:this.onPageUpKey(e);break;case`Enter`:case`NumpadEnter`:case`Space`:this.onTabEnterKey(e,t,n);break}},onTabArrowRightKey:function(e){var t=this.findNextHeaderAction(e.target.parentElement);t?this.changeFocusedTab(e,t):this.onTabHomeKey(e),e.preventDefault()},onTabArrowLeftKey:function(e){var t=this.findPrevHeaderAction(e.target.parentElement);t?this.changeFocusedTab(e,t):this.onTabEndKey(e),e.preventDefault()},onTabHomeKey:function(e){var t=this.findFirstHeaderAction();this.changeFocusedTab(e,t),e.preventDefault()},onTabEndKey:function(e){var t=this.findLastHeaderAction();this.changeFocusedTab(e,t),e.preventDefault()},onPageDownKey:function(e){this.scrollInView({index:this.$refs.nav.children.length-2}),e.preventDefault()},onPageUpKey:function(e){this.scrollInView({index:0}),e.preventDefault()},onTabEnterKey:function(e,t,n){this.changeActiveIndex(e,t,n),e.preventDefault()},findNextHeaderAction:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.nextElementSibling;return t?x(t,`data-p-disabled`)||x(t,`data-pc-section`)===`inkbar`?this.findNextHeaderAction(t):C(t,`[data-pc-section="headeraction"]`):null},findPrevHeaderAction:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.previousElementSibling;return t?x(t,`data-p-disabled`)||x(t,`data-pc-section`)===`inkbar`?this.findPrevHeaderAction(t):C(t,`[data-pc-section="headeraction"]`):null},findFirstHeaderAction:function(){return this.findNextHeaderAction(this.$refs.nav.firstElementChild,!0)},findLastHeaderAction:function(){return this.findPrevHeaderAction(this.$refs.nav.lastElementChild,!0)},changeActiveIndex:function(e,t,n){!this.getTabProp(t,`disabled`)&&this.d_activeIndex!==n&&(this.d_activeIndex=n,this.$emit(`update:activeIndex`,n),this.$emit(`tab-change`,{originalEvent:e,index:n}),this.scrollInView({index:n}))},changeFocusedTab:function(e,t){if(t&&(S(t),this.scrollInView({element:t}),this.selectOnFocus)){var n=parseInt(t.parentElement.dataset.pcIndex,10),r=this.tabs[n];this.changeActiveIndex(e,r,n)}},scrollInView:function(e){var t=e.element,n=e.index,r=n===void 0?-1:n,i=t||this.$refs.nav.children[r];i&&i.scrollIntoView&&i.scrollIntoView({block:`nearest`})},updateInkBar:function(){var e=this.$refs.nav.children[this.d_activeIndex];this.$refs.inkbar.style.width=b(e)+`px`,this.$refs.inkbar.style.left=y(e).left-y(this.$refs.nav).left+`px`},updateButtonState:function(){var e=this.$refs.content,t=e.scrollLeft,n=e.scrollWidth,r=b(e);this.isPrevButtonDisabled=t===0,this.isNextButtonDisabled=parseInt(t)===n-r},getVisibleButtonWidths:function(){var e=this.$refs;return[e.prevBtn,e.nextBtn].reduce(function(e,t){return t?e+b(t):e},0)}},computed:{tabs:function(){var e=this;return this.$slots.default().reduce(function(t,n){return e.isTabPanel(n)?t.push(n):n.children&&n.children instanceof Array&&n.children.forEach(function(n){e.isTabPanel(n)&&t.push(n)}),t},[])},prevButtonAriaLabel:function(){return this.$primevue.config.locale.aria?this.$primevue.config.locale.aria.previous:void 0},nextButtonAriaLabel:function(){return this.$primevue.config.locale.aria?this.$primevue.config.locale.aria.next:void 0}},directives:{ripple:h},components:{ChevronLeftIcon:E,ChevronRightIcon:T}};function k(e){"@babel/helpers - typeof";return k=typeof Symbol==`function`&&typeof Symbol.iterator==`symbol`?function(e){return typeof e}:function(e){return e&&typeof Symbol==`function`&&e.constructor===Symbol&&e!==Symbol.prototype?`symbol`:typeof e},k(e)}function A(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter(function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable})),n.push.apply(n,r)}return n}function j(e){for(var t=1;t<arguments.length;t++){var n=arguments[t]==null?{}:arguments[t];t%2?A(Object(n),!0).forEach(function(t){M(e,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):A(Object(n)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))})}return e}function M(e,t,n){return(t=N(t))in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function N(e){var t=P(e,`string`);return k(t)==`symbol`?t:t+``}function P(e,t){if(k(e)!=`object`||!e)return e;var n=e[Symbol.toPrimitive];if(n!==void 0){var r=n.call(e,t);if(k(r)!=`object`)return r;throw TypeError(`@@toPrimitive must return a primitive value.`)}return(t===`string`?String:Number)(e)}var F=[`tabindex`,`aria-label`],I=[`data-p-active`,`data-p-disabled`,`data-pc-index`],L=[`id`,`tabindex`,`aria-disabled`,`aria-selected`,`aria-controls`,`onClick`,`onKeydown`],R=[`tabindex`,`aria-label`],z=[`id`,`aria-labelledby`,`data-pc-index`,`data-p-active`];function B(r,o,h,g,v,y){var b=e(`ripple`);return i(),f(`div`,p({class:r.cx(`root`),role:`tablist`},r.ptmi(`root`)),[d(`div`,p({class:r.cx(`navContainer`)},r.ptm(`navContainer`)),[r.scrollable&&!v.isPrevButtonDisabled?m((i(),f(`button`,p({key:0,ref:`prevBtn`,type:`button`,class:r.cx(`prevButton`),tabindex:r.tabindex,"aria-label":y.prevButtonAriaLabel,onClick:o[0]||=function(){return y.onPrevButtonClick&&y.onPrevButtonClick.apply(y,arguments)}},j(j({},r.prevButtonProps),r.ptm(`prevButton`)),{"data-pc-group-section":`navbutton`}),[n(r.$slots,`previcon`,{},function(){return[(i(),a(s(r.prevIcon?`span`:`ChevronLeftIcon`),p({"aria-hidden":`true`,class:r.prevIcon},r.ptm(`prevIcon`)),null,16,[`class`]))]})],16,F)),[[b]]):c(``,!0),d(`div`,p({ref:`content`,class:r.cx(`navContent`),onScroll:o[1]||=function(){return y.onScroll&&y.onScroll.apply(y,arguments)}},r.ptm(`navContent`)),[d(`ul`,p({ref:`nav`,class:r.cx(`nav`)},r.ptm(`nav`)),[(i(!0),f(u,null,t(y.tabs,function(e,t){return i(),f(`li`,p({key:y.getKey(e,t),style:y.getTabProp(e,`headerStyle`),class:r.cx(`tab.header`,{tab:e,index:t}),role:`presentation`},{ref_for:!0},j(j(j({},y.getTabProp(e,`headerProps`)),y.getTabPT(e,`root`,t)),y.getTabPT(e,`header`,t)),{"data-pc-name":`tabpanel`,"data-p-active":v.d_activeIndex===t,"data-p-disabled":y.getTabProp(e,`disabled`),"data-pc-index":t}),[m((i(),f(`a`,p({id:y.getTabHeaderActionId(t),class:r.cx(`tab.headerAction`),tabindex:y.getTabProp(e,`disabled`)||!y.isTabActive(t)?-1:r.tabindex,role:`tab`,"aria-disabled":y.getTabProp(e,`disabled`),"aria-selected":y.isTabActive(t),"aria-controls":y.getTabContentId(t),onClick:function(n){return y.onTabClick(n,e,t)},onKeydown:function(n){return y.onTabKeyDown(n,e,t)}},{ref_for:!0},j(j({},y.getTabProp(e,`headerActionProps`)),y.getTabPT(e,`headerAction`,t))),[e.props&&e.props.header?(i(),f(`span`,p({key:0,class:r.cx(`tab.headerTitle`)},{ref_for:!0},y.getTabPT(e,`headerTitle`,t)),l(e.props.header),17)):c(``,!0),e.children&&e.children.header?(i(),a(s(e.children.header),{key:1})):c(``,!0)],16,L)),[[b]])],16,I)}),128)),d(`li`,p({ref:`inkbar`,class:r.cx(`inkbar`),role:`presentation`,"aria-hidden":`true`},r.ptm(`inkbar`)),null,16)],16)],16),r.scrollable&&!v.isNextButtonDisabled?m((i(),f(`button`,p({key:1,ref:`nextBtn`,type:`button`,class:r.cx(`nextButton`),tabindex:r.tabindex,"aria-label":y.nextButtonAriaLabel,onClick:o[2]||=function(){return y.onNextButtonClick&&y.onNextButtonClick.apply(y,arguments)}},j(j({},r.nextButtonProps),r.ptm(`nextButton`)),{"data-pc-group-section":`navbutton`}),[n(r.$slots,`nexticon`,{},function(){return[(i(),a(s(r.nextIcon?`span`:`ChevronRightIcon`),p({"aria-hidden":`true`,class:r.nextIcon},r.ptm(`nextIcon`)),null,16,[`class`]))]})],16,R)),[[b]]):c(``,!0)],16),d(`div`,p({class:r.cx(`panelContainer`)},r.ptm(`panelContainer`)),[(i(!0),f(u,null,t(y.tabs,function(e,t){return i(),f(u,{key:y.getKey(e,t)},[!r.lazy||y.isTabActive(t)?m((i(),f(`div`,p({key:0,id:y.getTabContentId(t),style:y.getTabProp(e,`contentStyle`),class:r.cx(`tab.content`,{tab:e}),role:`tabpanel`,"aria-labelledby":y.getTabHeaderActionId(t)},{ref_for:!0},j(j(j({},y.getTabProp(e,`contentProps`)),y.getTabPT(e,`root`,t)),y.getTabPT(e,`content`,t)),{"data-pc-name":`tabpanel`,"data-pc-index":t,"data-p-active":v.d_activeIndex===t}),[(i(),a(s(e)))],16,z)),[[_,r.lazy?!0:y.isTabActive(t)]]):c(``,!0)],64)}),128))],16)],16)}O.render=B;var V=g.extend({name:`tabpanel`,classes:{root:function(e){return[`p-tabpanel`,{"p-tabpanel-active":e.instance.active}]}}}),H={name:`TabPanel`,extends:{name:`BaseTabPanel`,extends:w,props:{value:{type:[String,Number],default:void 0},as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1},header:null,headerStyle:null,headerClass:null,headerProps:null,headerActionProps:null,contentStyle:null,contentClass:null,contentProps:null,disabled:Boolean},style:V,provide:function(){return{$pcTabPanel:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcTabs`],computed:{active:function(){return v(this.$pcTabs?.d_value,this.value)},id:function(){return`${this.$pcTabs?.$id}_tabpanel_${this.value}`},ariaLabelledby:function(){return`${this.$pcTabs?.$id}_tab_${this.value}`},attrs:function(){return p(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{id:this.id,tabindex:this.$pcTabs?.tabindex,role:`tabpanel`,"aria-labelledby":this.ariaLabelledby,"data-pc-name":`tabpanel`,"data-p-active":this.active}},ptParams:function(){return{context:{active:this.active}}}}};function U(e,t,l,d,h,g){var v,y;return g.$pcTabs?(i(),f(u,{key:1},[e.asChild?n(e.$slots,`default`,{key:1,class:o(e.cx(`root`)),active:g.active,a11yAttrs:g.a11yAttrs}):(i(),f(u,{key:0},[!((v=g.$pcTabs)!=null&&v.lazy)||g.active?m((i(),a(s(e.as),p({key:0,class:e.cx(`root`)},g.attrs),{default:r(function(){return[n(e.$slots,`default`)]}),_:3},16,[`class`])),[[_,(y=g.$pcTabs)!=null&&y.lazy?!0:g.active]]):c(``,!0)],64))],64)):n(e.$slots,`default`,{key:0})}H.render=U;export{O as n,H as t};