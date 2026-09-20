<script setup>
import { onMounted, ref } from 'vue'
import { errText, getJSON, postJSON, putJSON } from '../api'
const items = ref([])
const plate = ref('')
const enabled = ref(true)
const err = ref('')
const load = async () => { items.value = (await getJSON('/api/vehicles')).items }
const create = async () => {
  err.value = ''
  try {
    await postJSON('/api/vehicles', { plate: plate.value, enabled: enabled.value })
    plate.value = ''; enabled.value = true
    await load()
  } catch (e) { err.value = errText(e) }
}
const save = async (v) => {
  err.value = ''
  try { await putJSON(`/api/vehicles/${v.id}`, { plate: v.plate, enabled: !!v.enabled }); await load() }
  catch (e) { err.value = errText(e); await load() }
}
const disable = async (v) => {
  err.value = ''
  try { await postJSON(`/api/vehicles/${v.id}/disable`, {}); await load() }
  catch (e) { err.value = errText(e) }
}
onMounted(load)
</script>
<template>
  <div class="page"><h1>车辆</h1>
    <div class="panel">
      <label>车牌 <input v-model.trim="plate" placeholder="沪A·12345" /></label>
      <label><input type="checkbox" v-model="enabled" /> 启用</label>
      <button @click="create">创建</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <table>
      <tr><th>ID</th><th>车牌</th><th>状态</th><th>操作</th></tr>
      <tr v-for="v in items" :key="v.id">
        <td>#{{ v.id }}</td>
        <td><input v-model.trim="v.plate" /></td>
        <td><label><input type="checkbox" v-model="v.enabled" :true-value="1" :false-value="0" /> {{ v.enabled ? '启用' : '停用' }}</label></td>
        <td>
          <button @click="save(v)">保存</button>
          <button v-if="v.enabled" @click="disable(v)">停用</button>
        </td>
      </tr>
    </table>
  </div>
</template>
