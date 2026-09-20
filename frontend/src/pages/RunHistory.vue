<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const plate = ref('')          // 过滤车牌（精确）
const filterPlate = ref('')    // 已生效的过滤
const loading = ref(false)
const allPlates = ref([])      // 全量记录中出现过的车牌，供下拉选择

const load = async () => {
  loading.value = true
  try {
    // 上限取大，保证过滤条数与该牌实际写入条数一致
    const q = filterPlate.value
      ? `?plate=${encodeURIComponent(filterPlate.value)}&limit=100000`
      : '?limit=100000'
    const rows = (await getJSON(`/api/history${q}`)).items
    items.value = rows
    if (!filterPlate.value) {
      allPlates.value = [...new Set(rows.map(r => r.plate).filter(Boolean))].sort()
    }
  } finally { loading.value = false }
}

const plateOptions = computed(() => allPlates.value)

const applyFilter = async () => {
  filterPlate.value = plate.value.trim()
  await load()
}
const clearFilter = async () => {
  plate.value = ''
  filterPlate.value = ''
  await load()
}

onMounted(load)
</script>
<template>
  <div class="page"><h1>记录</h1>
    <div class="panel">
      <label>按车牌过滤
        <input v-model="plate" list="plate-list" placeholder="输入完整车牌" @keyup.enter="applyFilter" />
        <datalist id="plate-list">
          <option v-for="p in plateOptions" :key="p" :value="p" />
        </datalist>
      </label>
      <button @click="applyFilter">过滤</button>
      <button @click="clearFilter">清除</button>
      <span class="muted">当前 {{ filterPlate ? `车牌「${filterPlate}」` : '全部' }} · 共 {{ items.length }} 条</span>
    </div>
    <p v-if="loading" class="muted">加载中…</p>
    <table>
      <tr><th>记录</th><th>类型</th><th>当时车牌</th><th>车辆编号</th><th>时间</th></tr>
      <tr v-for="h in items" :key="h.id">
        <td>#{{ h.id }}</td>
        <td>{{ h.kind }}</td>
        <td>{{ h.plate || '—' }}</td>
        <td>{{ h.vehicle_id ? '#' + h.vehicle_id : '—' }}</td>
        <td>{{ h.created_at }}</td>
      </tr>
    </table>
    <p v-if="!loading && !items.length" class="muted">没有符合条件的记录。</p>
  </div>
</template>
