import{O as e,T as t,c as n,j as r,l as i,mt as a,u as o,x as s}from"./runtime-core.esm-bundler-DVgfZ4Qj.js";import{s as c}from"./button-cUalNMUU.js";import{Da as l}from"./index-9S-APUop.js";import{t as u}from"./basecomponent-DtEp-OoH.js";import{t as d}from"./timescircle-DS1a_NcY.js";var f=l.extend({name:`chip`,style:`
    .p-chip {
        display: inline-flex;
        align-items: center;
        background: dt('chip.background');
        color: dt('chip.color');
        border-radius: dt('chip.border.radius');
        padding-block: dt('chip.padding.y');
        padding-inline: dt('chip.padding.x');
        gap: dt('chip.gap');
    }

    .p-chip-icon {
        color: dt('chip.icon.color');
        font-size: dt('chip.icon.size');
        width: dt('chip.icon.size');
        height: dt('chip.icon.size');
    }

    .p-chip-image {
        border-radius: 50%;
        width: dt('chip.image.width');
        height: dt('chip.image.height');
        margin-inline-start: calc(-1 * dt('chip.padding.y'));
    }

    .p-chip:has(.p-chip-remove-icon) {
        padding-inline-end: dt('chip.padding.y');
    }

    .p-chip:has(.p-chip-image) {
        padding-block-start: calc(dt('chip.padding.y') / 2);
        padding-block-end: calc(dt('chip.padding.y') / 2);
    }

    .p-chip-remove-icon {
        cursor: pointer;
        font-size: dt('chip.remove.icon.size');
        width: dt('chip.remove.icon.size');
        height: dt('chip.remove.icon.size');
        color: dt('chip.remove.icon.color');
        border-radius: 50%;
        transition:
            outline-color dt('chip.transition.duration'),
            box-shadow dt('chip.transition.duration');
        outline-color: transparent;
    }

    .p-chip-remove-icon:focus-visible {
        box-shadow: dt('chip.remove.icon.focus.ring.shadow');
        outline: dt('chip.remove.icon.focus.ring.width') dt('chip.remove.icon.focus.ring.style') dt('chip.remove.icon.focus.ring.color');
        outline-offset: dt('chip.remove.icon.focus.ring.offset');
    }
`,classes:{root:`p-chip p-component`,image:`p-chip-image`,icon:`p-chip-icon`,label:`p-chip-label`,removeIcon:`p-chip-remove-icon`}}),p={name:`Chip`,extends:{name:`BaseChip`,extends:u,props:{label:{type:[String,Number],default:null},icon:{type:String,default:null},image:{type:String,default:null},removable:{type:Boolean,default:!1},removeIcon:{type:String,default:void 0}},style:f,provide:function(){return{$pcChip:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`remove`],data:function(){return{visible:!0}},methods:{onKeydown:function(e){(e.key===`Enter`||e.key===`Backspace`)&&this.close(e)},close:function(e){this.visible=!1,this.$emit(`remove`,e)}},computed:{dataP:function(){return c({removable:this.removable})}},components:{TimesCircleIcon:d}},m=[`aria-label`,`data-p`],h=[`src`];function g(c,l,u,d,f,p){return f.visible?(t(),o(`div`,s({key:0,class:c.cx(`root`),"aria-label":c.label},c.ptmi(`root`),{"data-p":p.dataP}),[e(c.$slots,`default`,{},function(){return[c.image?(t(),o(`img`,s({key:0,src:c.image},c.ptm(`image`),{class:c.cx(`image`)}),null,16,h)):c.$slots.icon?(t(),n(r(c.$slots.icon),s({key:1,class:c.cx(`icon`)},c.ptm(`icon`)),null,16,[`class`])):c.icon?(t(),o(`span`,s({key:2,class:[c.cx(`icon`),c.icon]},c.ptm(`icon`)),null,16)):i(``,!0),c.label===null?i(``,!0):(t(),o(`div`,s({key:3,class:c.cx(`label`)},c.ptm(`label`)),a(c.label),17))]}),c.removable?e(c.$slots,`removeicon`,{key:0,removeCallback:p.close,keydownCallback:p.onKeydown},function(){return[(t(),n(r(c.removeIcon?`span`:`TimesCircleIcon`),s({class:[c.cx(`removeIcon`),c.removeIcon],onClick:p.close,onKeydown:p.onKeydown},c.ptm(`removeIcon`)),null,16,[`class`,`onClick`,`onKeydown`]))]}):i(``,!0)],16,m)):i(``,!0)}p.render=g;export{p as t};