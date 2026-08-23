<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, Filler } from 'chart.js'
import vSelect from 'vue-select'
import 'vue-select/dist/vue-select.css';
import VueFeather from 'vue-feather';

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, Filler)

const API_BASE_URL = '';
const route = useRoute()
const deviceId = route.params.id

const selectedSensor = ref('temperature')
const selectedRange = ref(24)
const chartDataRaw = ref({ labels: [], data: [] })
const loading = ref(true)

const sensorIcons = {
  temperature: 'thermometer',
  humidity: 'droplet',
  pressure: 'target',
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

const chartData = computed(() => {
  const now = new Date();
  const rangeHours = selectedRange.value;
  const startTime = new Date(now.getTime() - rangeHours * 60 * 60 * 1000);

  let intervalMinutes;
  if (rangeHours <= 1) intervalMinutes = 5;
  else if (rangeHours <= 6) intervalMinutes = 15;
  else if (rangeHours <= 24) intervalMinutes = 60;
  else intervalMinutes = 6 * 60;
  const intervalMillis = intervalMinutes * 60 * 1000;

  const fullLabels = [];
  let currentTime = new Date(Math.floor(startTime.getTime() / intervalMillis) * intervalMillis);
  while (currentTime <= now) {
    fullLabels.push(new Date(currentTime));
    currentTime.setTime(currentTime.getTime() + intervalMillis);
  }
  if (fullLabels.length > 0 && fullLabels[fullLabels.length - 1] < now) {
    fullLabels.push(currentTime);
  }

  const fullData = Array(fullLabels.length).fill(null);

  if (chartDataRaw.value.labels && chartDataRaw.value.labels.length > 0) {
    const dataPoints = chartDataRaw.value.labels.map((ts, i) => ({
      time: new Date(ts).getTime(),
      value: chartDataRaw.value.data[i]
    }));

    const buckets = Array.from({ length: fullLabels.length }, () => []);

    dataPoints.forEach(point => {
      let bucketIdx = -1;
      for (let i = 0; i < fullLabels.length; i++) {
          if (point.time >= fullLabels[i].getTime()) {
              bucketIdx = i;
          } else {
              break;
          }
      }

      if (bucketIdx !== -1) {
        buckets[bucketIdx].push(point.value);
      }
    });

    buckets.forEach((bucket, index) => {
      if (bucket.length > 0) {
        const sum = bucket.reduce((a, b) => a + b, 0);
        fullData[index] = sum / bucket.length;
      }
    });
  }

  const formatLabel = (date) => {
    if (rangeHours > 48) {
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }
    return date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
  };

  return {
    labels: fullLabels.map(formatLabel),
    datasets: [{
      label: sensorOptions.find(opt => opt.value === selectedSensor.value)?.text || selectedSensor.value,
      backgroundColor: 'rgba(47, 127, 214, 0.15)',
      borderColor: '#2f7fd6',
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2,
      tension: 0.3,
      fill: true,
      data: fullData,
    }]
  };
});

const sunExposureSummary = computed(() => {
  const risks = chartDataRaw.value.sun_exposure
  if (selectedSensor.value !== 'temperature' || !risks || risks.length === 0) return null
  const highCount = risks.filter((r) => r === 'high').length
  if (highCount === 0) return null
  return Math.round((100 * highCount) / risks.length)
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      ticks: {
        maxTicksLimit: 15 // Prevents the x-axis from getting too crowded
      }
    },
    y: {
      grace: '10%' // Add 10% padding to the top and bottom of the y-axis
    }
  }
}))

const selectedSensorUnit = computed(() => {
  switch (selectedSensor.value) {
    case 'temperature': return '°C';
    case 'humidity': return '%';
    case 'pressure': return 'hPa';
    case 'wind_speed': return 'km/h';
    default: return '';
  }
});

const tableData = computed(() => {
  if (!chartDataRaw.value.labels || chartDataRaw.value.labels.length === 0) {
    return [];
  }
  return chartDataRaw.value.labels
    .map((ts, index) => ({
      timestamp: new Date(ts).toLocaleString(),
      value: chartDataRaw.value.data[index]
    }))
    .reverse();
});

const stats = computed(() => {
  const data = chartDataRaw.value.data;
  if (!data || data.length === 0) {
    return { min: 0, max: 0, avg: 0 };
  }
  const cleanData = data.filter(v => v !== null);
  if (cleanData.length === 0) {
    return { min: 0, max: 0, avg: 0 };
  }
  const sum = cleanData.reduce((a, b) => a + b, 0);
  const avg = (sum / cleanData.length).toFixed(1);
  const min = Math.min(...cleanData).toFixed(1);
  const max = Math.max(...cleanData).toFixed(1);
  return { min, max, avg };
});

watch(selectedSensor, fetchChartData)
watch(selectedRange, fetchChartData)

onMounted(fetchChartData)
</script>

<template>
  <main class="page">
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

    <div class="stats-container" v-if="!loading && chartDataRaw.data.length > 0">
      <div class="stat-item">
        <span class="label">Min</span>
        <span class="value">{{ stats.min }} {{ selectedSensorUnit }}</span>
      </div>
      <div class="stat-item">
        <span class="label">Max</span>
        <span class="value">{{ stats.max }} {{ selectedSensorUnit }}</span>
      </div>
      <div class="stat-item">
        <span class="label">Moyenne</span>
        <span class="value">{{ stats.avg }} {{ selectedSensorUnit }}</span>
      </div>
    </div>

    <p v-if="sunExposureSummary" class="sun-note">
      <vue-feather type="sun" size="15"></vue-feather>
      Environ {{ sunExposureSummary }}% de ces mesures ont été prises avec le soleil haut : la
      température affichée peut être surestimée sur ces périodes (voir la page d'accueil pour
      une estimation corrigée sur la mesure en cours).
    </p>

    <div class="chart-container card">
      <Line v-if="!loading && chartData.datasets[0].data.length > 0" :data="chartData" :options="chartOptions" />
      <p v-if="loading">Chargement du graphique...</p>
      <p v-if="!loading && chartData.datasets[0].data.length === 0">Aucune donnée pour cette sélection.</p>
    </div>

    <div class="data-table-container" v-if="!loading && tableData.length > 0">
      <h3>Relevés de données brutes</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Horodatage</th>
            <th>Valeur ({{ selectedSensorUnit }})</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in tableData" :key="row.timestamp">
            <td>{{ row.timestamp }}</td>
            <td>{{ row.value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>

<style>
/* Global override for vue-select to match the app's theme */
.control-group {
  --vs-controls-color: var(--color-text);
  --vs-controls-bg: var(--color-surface);
  --vs-border-color: var(--color-border);
  --vs-border-radius: 8px;

  --vs-dropdown-bg: var(--color-surface);
  --vs-dropdown-color: var(--color-text);
  --vs-dropdown-option-color: var(--color-text);

  --vs-dropdown-option--active-bg: var(--color-surface-muted);
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
h1 {
  margin-bottom: 1.5rem;
}

.controls {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}
.control-group {
  display: flex;
  flex-direction: column;
  min-width: 220px;
}
.control-group label {
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.sun-note {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
  color: var(--color-warning-text);
  padding: 0.7rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.sun-note svg {
  flex-shrink: 0;
}

.chart-container {
  position: relative;
  height: 55vh;
  width: 100%;
  padding: 1.25rem;
}

.data-table-container {
  margin-top: 2.5rem;
}

.data-table-container h3 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.data-table th,
.data-table td {
  border-bottom: 1px solid var(--color-border);
  padding: 0.65rem 0.75rem;
  text-align: left;
}

.data-table thead {
  background-color: var(--color-surface-muted);
}

.data-table th {
  color: var(--color-heading);
  font-weight: 600;
}

.stats-container {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}
.stat-item {
  text-align: center;
}
.stat-item .label {
  display: block;
  font-size: 0.85em;
  color: var(--color-text-muted);
  margin-bottom: 0.25rem;
}
.stat-item .value {
  display: block;
  font-size: 1.4em;
  font-weight: 600;
  color: var(--color-heading);
}

@media (max-width: 768px) {
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
