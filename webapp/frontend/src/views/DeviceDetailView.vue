<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js'
import vSelect from 'vue-select'
import 'vue-select/dist/vue-select.css';
import VueFeather from 'vue-feather';

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement)

const API_BASE_URL = 'http://192.168.1.20:5001' // Temp IP
const route = useRoute()
const deviceId = route.params.id

const selectedSensor = ref('temperature')
const selectedRange = ref(24)
const chartDataRaw = ref({ labels: [], data: [] })
const loading = ref(true)

const sensorIcons = {
  temperature: 'thermometer',
  humidity: 'droplet',
  pressure: 'activity',
  wind_speed: 'wind',
};

const sensorOptions = [
  { value: 'temperature', text: 'Température' },
  { value: 'humidity', text: 'Humidité' },
  { value: 'pressure', text: 'Pression' },
  { value: 'wind_speed', text: 'Vitesse du vent' },
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
    label: sensorOptions.find(opt => opt.value === selectedSensor.value)?.text || selectedSensor.value,
    backgroundColor: '#f87979',
    borderColor: '#f87979',
    data: chartDataRaw.value.data,
  }]
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      grace: '10%' // Ajoute 10% de marge en haut et en bas de l'échelle
    }
  }
}))

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
        <v-select
            id="sensor-select"
            v-model="selectedSensor"
            :options="sensorOptions"
            :reduce="option => option.value"
            label="text"
            :clearable="false"
            :searchable="false"
        >
          <template #option="{ text, value }">
            <span class="select-option">
              <vue-feather :type="sensorIcons[value]" size="16"></vue-feather>
              <span>{{ text }}</span>
            </span>
          </template>
          <template #selected-option="{ text, value }">
             <span class="select-option">
              <vue-feather :type="sensorIcons[value]" size="16"></vue-feather>
              <span>{{ text }}</span>
            </span>
          </template>
        </v-select>
      </div>
      <div class="control-group">
        <label for="range-select">Période :</label>
        <v-select
            id="range-select"
            v-model="selectedRange"
            :options="rangeOptions"
            :reduce="option => option.value"
            label="text"
            :clearable="false"
            :searchable="false"
        ></v-select>
      </div>
    </div>

    <div class="chart-container">
      <Line v-if="!loading && chartData.datasets[0].data.length > 0" :data="chartData" :options="chartOptions" />
      <p v-if="loading">Chargement du graphique...</p>
      <p v-if="!loading && chartData.datasets[0].data.length === 0">Aucune donnée pour cette sélection.</p>
    </div>
  </main>
</template>

<style>
/* Global override for vue-select to match the app's theme */
.control-group {
  --vs-controls-color: var(--color-text);
  --vs-controls-bg: var(--color-background-soft);
  --vs-border-color: var(--color-border);
  --vs-border-radius: 4px;

  --vs-dropdown-bg: var(--color-background-soft);
  --vs-dropdown-color: var(--color-text);
  --vs-dropdown-option-color: var(--color-text);

  --vs-dropdown-option--active-bg: var(--color-background-mute);
  --vs-dropdown-option--active-color: var(--color-heading);

  --vs-search-input-color: var(--color-text);
  --vs-selected-color: var(--color-heading);
  --vs-line-height: 1.5;
}

.vs__dropdown-toggle {
  padding: 0.25rem 0.5rem;
}

.select-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>

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
  min-width: 250px; /* Give select some base width */
}
.control-group label {
  margin-bottom: 0.5rem;
}

.chart-container {
  position: relative;
  height: 60vh;
  width: 100%;
}

@media (max-width: 768px) {
  main {
    padding: 1rem;
  }
  .controls {
    flex-direction: column;
    gap: 1rem;
  }
  .control-group {
    min-width: auto;
    width: 100%;
  }
}
</style>
