<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement)

const API_BASE_URL = 'http://192.168.1.20:5001' // Temp IP
const route = useRoute()
const deviceId = route.params.id

const selectedSensor = ref('temperature')
const selectedRange = ref(24)
const chartDataRaw = ref({ labels: [], data: [] })
const loading = ref(true)

const sensorOptions = [
  { value: 'temperature', text: '🌡️ Température' },
  { value: 'humidity', text: '💧 Humidité' },
  { value: 'pressure', text: '🌬️ Pression' },
  { value: 'wind_speed', text: '💨 Vitesse du vent' },
]
const rangeOptions = [
  { value: 1, text: 'Dernière heure' },
  { value: 6, text: '6 dernières heures' },
  { value: 24, text: '24 dernières heures' },
  { value: 168, text: '7 derniers jours' },
]

const fetchChartData = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/history?sensor=${selectedSensor.value}&range=${selectedRange.value}`)
    chartDataRaw.value = await response.json()
  } catch (error) {
    console.error("Erreur lors de la récupération de l'historique:", error)
  } finally {
    loading.value = false
  }
}

const chartData = computed(() => ({
  labels: chartDataRaw.value.labels.map(ts => new Date(ts).toLocaleTimeString()),
  datasets: [{
    label: sensorOptions.find(opt => opt.value === selectedSensor.value).text,
    backgroundColor: '#f87979',
    borderColor: '#f87979',
    data: chartDataRaw.value.data,
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
}

watch(selectedSensor, fetchChartData)
watch(selectedRange, fetchChartData)

onMounted(fetchChartData)
</script>

<template>
  <main>
    <h1>Détail de l'appareil #{{ deviceId }}</h1>

    <div class="controls">
      <div class="control-group">
        <label for="sensor-select">Capteur :</label>
        <select id="sensor-select" v-model="selectedSensor">
          <option v-for="option in sensorOptions" :key="option.value" :value="option.value">
            {{ option.text }}
          </option>
        </select>
      </div>
      <div class="control-group">
        <label for="range-select">Période :</label>
        <select id="range-select" v-model="selectedRange">
          <option v-for="option in rangeOptions" :key="option.value" :value="option.value">
            {{ option.text }}
          </option>
        </select>
      </div>
    </div>

    <div class="chart-container">
      <Line v-if="!loading && chartData.datasets[0].data.length > 0" :data="chartData" :options="chartOptions" />
      <p v-if="loading">Chargement du graphique...</p>
      <p v-if="!loading && chartData.datasets[0].data.length === 0">Aucune donnée pour cette sélection.</p>
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
}
.controls {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}
.control-group {
  display: flex;
  flex-direction: column;
}
.control-group label {
  margin-bottom: 0.5rem;
}
.control-group select {
  padding: 0.5rem;
  border-radius: 4px;
}
.chart-container {
  position: relative;
  height: 60vh;
  width: 100%;
}
</style>
