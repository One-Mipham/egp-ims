<script setup lang="ts">
const props = withDefaults(defineProps<{
  cat: any
  selectedId: number | null
  expandedIds: Set<number>
  depth?: number
}>(), { depth: 0 })

defineEmits<{
  select: [id: number]
  toggle: [id: number]
  add: [parentId: number]
  edit: [cat: any]
  remove: [cat: any]
}>()
</script>

<template>
  <div>
    <div
      class="flex items-center justify-between px-3 py-1.5 text-xs cursor-pointer hover:bg-zinc-100 transition-colors group"
      :class="selectedId === cat.id ? 'bg-blue-100 text-blue-700 font-bold' : 'text-zinc-600'"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
      @click="$emit('select', cat.id)"
    >
      <div class="flex items-center gap-1 min-w-0">
        <button
          v-if="cat.children?.length"
          @click.stop="$emit('toggle', cat.id)"
          class="text-zinc-400 hover:text-zinc-600 w-4 text-center shrink-0"
        >{{ expandedIds.has(cat.id) ? '▾' : '▸' }}</button>
        <span v-else class="w-4 shrink-0"></span>
        <span v-if="cat.is_system" title="系统预置" class="text-[10px] shrink-0">🔒</span>
        <span class="truncate">{{ cat.name }}</span>
        <span class="text-[10px] text-zinc-400 shrink-0">({{ cat.article_count }})</span>
      </div>
      <div class="hidden group-hover:flex items-center gap-0.5 shrink-0">
        <button v-if="!cat.is_system" @click.stop="$emit('edit', cat)" title="编辑" class="text-[10px] px-1 text-zinc-400 hover:text-blue-600">✎</button>
        <button @click.stop="$emit('add', cat.id)" title="添加子分类" class="text-[10px] px-1 text-zinc-400 hover:text-green-600">+</button>
        <button v-if="!cat.is_system" @click.stop="$emit('remove', cat)" title="删除" class="text-[10px] px-1 text-zinc-400 hover:text-red-500">×</button>
      </div>
    </div>
    <template v-if="cat.children?.length && expandedIds.has(cat.id)">
      <CategoryTreeNode
        v-for="child in cat.children"
        :key="child.id"
        :cat="child"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        :depth="depth + 1"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @add="$emit('add', $event)"
        @edit="$emit('edit', $event)"
        @remove="$emit('remove', $event)"
      />
    </template>
  </div>
</template>
