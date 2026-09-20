<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const vehicles = ref([])
const vehicle_id = ref('')
const out = ref(null)
const err = ref('')

onMounted(async () => {
  vehicles.value = (await getJSON('/api/vehicles')).items.filter(v => v.active)
})

const errText = (e) => {
  try { return JSON.parse(e.message).detail || e.message } catch { return e.message }
}

const run = async () => {
  err.value = ''
  out.value = null
  if (!vehicle_id.value) { err.value = '请先选定车辆再落表'; return }
  try {
    out.value = await postJSON('/api/fare', {
      distance_km: distance_km.value, slow_min: slow_min.value, night: night.value,
      vehicle_id: Number(vehicle_id.value), persist: true,
    })
  } catch (e) { err.value = errText(e) }
}
</script>
<template>
  <div class="page"><h1>打表落表</h1>
    <div class="panel">
      <label>车辆
        <select v-model="vehicle_id">
          <option value="" disabled>请选择启用中的车辆</option>
          <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.plate }}（#{{ v.id }}）</option>
        </select>
      </label>
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <button @click="run">计算并落表</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <template v-if="out">
      <p class="hero-num">¥{{ out.total }}</p>
      <p class="muted">记录 #{{ out.run_id }} · 车辆 {{ out.plate }}（#{{ out.vehicle_id }}）</p>
    </template>
  </div>
</template>
