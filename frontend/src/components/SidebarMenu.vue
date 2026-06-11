<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import type { MenuSection } from '@/config/menuConfig'

const props = defineProps<{
  sections: MenuSection[]
  userRole: string
}>()

const emit = defineEmits<{
  locked: [message: string]
}>()

const route = useRoute()

// Default to 知识库 (index 13), or find section matching current route
function findSectionForRoute(): MenuSection | undefined {
  for (const section of props.sections) {
    for (const item of section.items) {
      if (item.to === route.path) return section
      if (item.children?.some(c => c.to === route.path)) return section
    }
  }
  return undefined
}

// Get enabled modules from localStorage (set on login or subscription change)
function getEnabledModules(): string[] {
  try {
    const raw = localStorage.getItem('enabledModules')
    if (raw) return JSON.parse(raw)
  } catch (_) { /* ignore */ }
  return []
}

const isTrialing = computed(() => localStorage.getItem('subscriptionStatus') === 'trialing')

// Filter sections by user role AND module subscription
const visibleSections = computed(() =>
  props.sections.filter(s => {
    // Role check
    if (s.roles && s.roles.length > 0 && !s.roles.includes(props.userRole)) return false
    // Module subscription check (knowledge is always free; trial sees all)
    if (isTrialing.value) return true
    if (!s.module || s.module === 'knowledge') return true
    const enabled = getEnabledModules()
    if (enabled.length === 0) return true  // no data yet, show all
    return enabled.includes(s.module)
  })
)

const activeSection = ref<MenuSection>(findSectionForRoute() || visibleSections.value[0] || props.sections[0])

// Keep active section in sync with route changes
watch(() => route.path, () => {
  const match = findSectionForRoute()
  if (match) activeSection.value = match
})

const expandedSubmenus = ref<Set<string>>(new Set())

function selectSection(section: MenuSection) {
  activeSection.value = section
}

function toggleSubmenu(key: string) {
  const set = expandedSubmenus.value
  if (set.has(key)) set.delete(key)
  else set.add(key)
  expandedSubmenus.value = new Set(set)
}

function isLocked(item: { roles?: string[] }): boolean {
  if (!item.roles || item.roles.length === 0) return false
  return !item.roles.includes(props.userRole)
}

function handleLockedClick(item: { lockedMessage?: string }) {
  emit('locked', item.lockedMessage || '您无权访问此功能')
}

// Find which top-level item (or child) matches current route
function isItemActive(item: { to?: string; children?: Array<{ to: string }> }): boolean {
  if (item.to && route.path === item.to) return true
  if (item.children?.some(c => c.to === route.path)) return true
  return false
}
</script>

<template>
  <div class="flex flex-1 overflow-hidden">
    <!-- Column 1: 一级目录 -->
    <div class="flex-1 border-r border-white/10 overflow-y-auto sidebar-col1-bg">
      <button
        v-for="section in visibleSections"
        :key="section.title"
        @click="selectSection(section)"
        class="w-full flex flex-col items-center gap-1 px-1 py-2.5 text-[10px] transition-colors tracking-wide"
        :class="activeSection.title === section.title
          ? 'sidebar-col1-active'
          : 'sidebar-col1-item'"
      >
        <i :class="[section.icon, 'text-sm']" />
        <span class="leading-tight text-center">{{ section.shortTitle }}</span>
      </button>
    </div>

    <!-- Column 2: 二级目录 -->
    <div class="flex-1 overflow-y-auto py-1">
      <!-- Active section title -->
      <div class="px-3 py-2 text-[11px] font-semibold sidebar-col2-header tracking-wide border-b border-white/5">
        {{ activeSection.title }}
      </div>

      <template v-for="item in activeSection.items" :key="item.label">
        <!-- Item with children (3rd level) — hidden if locked -->
        <div v-if="item.children && item.children.length && !isLocked(item)">
          <button
            @click="toggleSubmenu(item.label)"
            class="w-full flex items-center gap-2 pl-3 pr-2 py-1.5 text-[10px] sidebar-item-sub transition-colors tracking-wide"
          >
            <i :class="['pi', item.icon, 'text-[10px] w-4 text-center']" />
            <span class="flex-1 text-left">{{ item.label }}</span>
            <i
              :class="[
                'pi text-[10px] sidebar-item-sub transition-transform',
                expandedSubmenus.has(item.label) ? 'pi-angle-up' : 'pi-angle-down'
              ]"
            />
          </button>
          <div v-show="expandedSubmenus.has(item.label)" class="sidebar-submenu-bg">
            <router-link
              v-for="child in item.children"
              :key="child.to"
              :to="child.to"
              class="flex items-center gap-2 pl-9 pr-2 py-1 text-[10px] sidebar-item-sub transition-colors"
              :class="{ 'sidebar-item-active': route.path === child.to }"
            >
              {{ child.label }}
            </router-link>
          </div>
        </div>

        <!-- Direct link item (unlocked) -->
        <router-link
          v-else-if="item.to && !isLocked(item)"
          :to="item.to"
          class="flex items-center gap-2 pl-3 pr-2 py-1.5 text-[10px] sidebar-item-sub transition-colors"
          :class="{ 'sidebar-item-active': route.path === item.to }"
        >
          <i :class="['pi', item.icon, 'text-[10px] w-4 text-center']" />
          <span>{{ item.label }}</span>
        </router-link>

      </template>
    </div>
  </div>
</template>
