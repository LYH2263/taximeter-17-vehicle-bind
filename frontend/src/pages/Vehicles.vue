<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON, patchJSON } from '../api'

const items = ref([])
const newPlate = ref('')
const err = ref('')
const loading = ref(false)

const errText = (e) => {
  try { return JSON.parse(e.message).detail || e.message } catch { return e.message }
}
const load = async () => {
  items.value = (await getJSON('/api/vehicles')).items.map(v => ({ ...v, _edit: v.plate }))
}

const create = async () => {
  err.value = ''
  const plate = newPlate.value.trim()
  if (!plate) { err.value = '车牌不能为空'; return }
  loading.value = true
  try {
    await postJSON('/api/vehicles', { plate, active: true })
    newPlate.value = ''
    await load()
  } catch (e) { err.value = errText(e) } finally { loading.value = false }
}

const rename = async (v) => {
  err.value = ''
  const plate = v._edit.trim()
  if (!plate) { err.value = '车牌不能为空'; return }
  if (plate === v.plate) { v._edit = v.plate; return }
  try {
    await patchJSON(`/api/vehicles/${v.id}`, { plate })
    await load()
  } catch (e) { err.value = errText(e); await load() }
}

const toggle = async (v) => {
  err.value = ''
  try {
    await patchJSON(`/api/vehicles/${v.id}`, { active: !v.active })
    await load()
  } catch (e) { err.value = errText(e); await load() }
}

onMounted(load)
</script>
<template>
  <div class="page"><h1>车辆</h1>
    <div class="panel">
      <label>新车牌 <input v-model="newPlate" placeholder="如 京A12345" @keyup.enter="create" /></label>
      <button :disabled="loading" @click="create">新增车辆</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <table>
      <tr><th>编号</th><th>车牌</th><th>状态</th><th>操作</th></tr>
      <tr v-for="v in items" :key="v.id">
        <td>#{{ v.id }}</td>
        <td>
          <input v-model="v._edit" @keyup.enter="rename(v)" />
          <button @click="rename(v)">改车牌</button>
        </td>
        <td>
          <span :class="v.active ? 'tag-on' : 'tag-off'">{{ v.active ? '启用中' : '已停用' }}</span>
        </td>
        <td>
          <button v-if="v.active" @click="toggle(v)">停用</button>
          <button v-else @click="toggle(v)">重新启用</button>
        </td>
      </tr>
    </table>
    <p v-if="!items.length" class="muted">还没有车辆，先新增一辆。</p>
  </div>
</template>
