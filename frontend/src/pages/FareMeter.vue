<script setup>
import { computed, onMounted, ref } from 'vue'
import { errText, getJSON, postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const vehicles = ref([])
const vehicle_id = ref(null)
const out = ref(null)
const err = ref('')
const enabledVehicles = computed(() => vehicles.value.filter(v => v.enabled))
const trial = async () => {
  err.value = ''; out.value = null
  try { out.value = await postJSON('/api/fare', { distance_km: distance_km.value, slow_min: slow_min.value, night: night.value, persist: false }) }
  catch (e) { err.value = errText(e) }
}
const run = async () => {
  err.value = ''; out.value = null
  if (!vehicle_id.value) { err.value = '请先选择启用中的车辆再落表'; return }
  try {
    out.value = await postJSON('/api/fare', { distance_km: distance_km.value, slow_min: slow_min.value, night: night.value, persist: true, vehicle_id: vehicle_id.value })
  } catch (e) { err.value = errText(e) }
}
onMounted(async () => {
  vehicles.value = (await getJSON('/api/vehicles')).items
  if (enabledVehicles.value.length) vehicle_id.value = enabledVehicles.value[0].id
})
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <label>车辆
        <select v-model="vehicle_id">
          <option :value="null">未选择</option>
          <option v-for="v in enabledVehicles" :key="v.id" :value="v.id">#{{ v.id }} {{ v.plate }}</option>
        </select>
      </label>
      <button @click="trial">试算</button>
      <button @click="run" :disabled="!vehicle_id">落表</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <div v-if="out">
      <p class="hero-num">¥{{ out.total }}</p>
      <p v-if="out.run_id">已落表 #{{ out.run_id }} · 车牌 {{ out.plate }}</p>
    </div>
  </div>
</template>
