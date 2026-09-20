<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const total = ref(0)
const plate = ref('')
const load = async () => {
  const p = plate.value.trim()
  const q = p ? `?limit=200&plate=${encodeURIComponent(p)}` : '?limit=200'
  const d = await getJSON(`/api/history${q}`)
  items.value = d.items
  total.value = d.total
}
const clear = async () => { plate.value = ''; await load() }
onMounted(load)
</script>
<template>
  <div class="page"><h1>记录</h1>
    <div class="panel">
      <label>车牌过滤 <input v-model.trim="plate" placeholder="输入当时车牌" @keyup.enter="load" /></label>
      <button @click="load">查询</button>
      <button @click="clear">清除</button>
      <span> 共 {{ total }} 条</span>
    </div>
    <table>
      <tr><th>ID</th><th>类型</th><th>车牌</th><th>时间</th></tr>
      <tr v-for="h in items" :key="h.id">
        <td>#{{ h.id }}</td><td>{{ h.kind }}</td><td>{{ h.plate || '—' }}</td><td>{{ h.created_at }}</td>
      </tr>
    </table>
  </div>
</template>
