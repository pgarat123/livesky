<script setup>
import { ref, onMounted, computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler } from 'chart.js'
import StatCard from '../components/StatCard.vue'
import VueFeather from 'vue-feather'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler)

const loading = ref(true)
const records = ref(null)
const climatology = ref([])
const yearlyAverages = ref([])
const deviceId = ref(null)

const MONTH_NAMES = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']

const formatDate = (ts) => ts ? new Date(ts).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'

const loadAll = async () => {
  loading.value = true
  try {
    const devicesRes = await fetch('/api/devices')
    const devices = await devicesRes.json()
    deviceId.value = devices[0]?.device_id ?? null

    const qs = deviceId.value ? `?device_id=${deviceId.value}` : ''
    const [recordsRes, climatologyRes, yearlyRes] = await Promise.all([
      fetch(`/api/stats/records${qs}`),
      fetch(`/api/stats/climatology${qs}`),
      fetch(`/api/stats/yearly-comparison${qs}`),
    ])
    records.value = await recordsRes.json()
    climatology.value = await climatologyRes.json()
    yearlyAverages.value = await yearlyRes.json()
  } catch (error) {
    console.error('Erreur lors du chargement des statistiques:', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

const climatologyChart = computed(() => {
  const byMonth = new Map(climatology.value.map((m) => [m.month, m]))
  const labels = []
  const avg = []
  const min = []
  const max = []
  for (let m = 1; m <= 12; m++) {
    const entry = byMonth.get(m)
    labels.push(MONTH_NAMES[m - 1])
    avg.push(entry?.avg_temp ?? null)
    min.push(entry?.min_temp ?? null)
    max.push(entry?.max_temp ?? null)
  }
  return {
    labels,
    datasets: [
      { label: 'Max', data: max, borderColor: '#dc6803', backgroundColor: 'transparent', borderWidth: 1, pointRadius: 2, borderDash: [4, 3] },
      { label: 'Moyenne', data: avg, borderColor: '#2f7fd6', backgroundColor: '#2f7fd622', borderWidth: 2, pointRadius: 3, fill: '+1' },
      { label: 'Min', data: min, borderColor: '#2563eb', backgroundColor: 'transparent', borderWidth: 1, pointRadius: 2, borderDash: [4, 3] },
    ],
  }
})

const climatologyOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' } },
  scales: { y: { title: { display: true, text: '°C' } } },
}

const yearsAvailable = computed(() => [...new Set(yearlyAverages.value.map((d) => d.year))].sort())

const yearlyChart = computed(() => {
  const years = yearsAvailable.value
  const palette = ['#2f7fd6', '#dc6803', '#16a34a', '#7c3aed']
  const datasets = years.map((year, i) => {
    const points = Array(366).fill(null)
    yearlyAverages.value
      .filter((d) => d.year === year)
      .forEach((d) => { points[d.day_of_year - 1] = d.avg_temp })
    return {
      label: String(year),
      data: points,
      borderColor: palette[i % palette.length],
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      pointRadius: 0,
      spanGaps: true,
    }
  })
  return {
    labels: Array.from({ length: 366 }, (_, i) => i + 1),
    datasets,
  }
}

)

const yearlyOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' } },
  scales: {
    x: { title: { display: true, text: 'Jour de l\'année' }, ticks: { maxTicksLimit: 12 } },
    y: { title: { display: true, text: '°C' } },
  },
}
</script>

<template>
  <main class="page">
    <h1>Historique &amp; records</h1>
    <p class="intro">Ce que l'année de mesures déjà collectée par la station raconte.</p>

    <div v-if="loading" class="loading">Chargement…</div>

    <template v-else>
      <section class="section">
        <h2>Records</h2>
        <div class="records-grid" v-if="records">
          <StatCard icon="thermometer" label="Température max" :value="records.temperature_max.value" unit="°C" :sub="formatDate(records.temperature_max.timestamp)">
            <template #footer>
              <p v-if="records.temperature_max.sun_exposure_risk === 'high'" class="record-caveat">
                <vue-feather type="sun" size="13"></vue-feather>
                Probablement gonflé par le soleil (mesure de jour, capteur non abrité)
              </p>
            </template>
          </StatCard>
          <StatCard icon="thermometer" label="Température min" :value="records.temperature_min.value" unit="°C" :sub="formatDate(records.temperature_min.timestamp)" />
          <StatCard icon="droplet" label="Humidité max" :value="records.humidity_max.value" unit="%" :sub="formatDate(records.humidity_max.timestamp)" />
          <StatCard icon="target" label="Pression max" :value="records.pressure_max.value" unit="hPa" :sub="formatDate(records.pressure_max.timestamp)" />
          <StatCard icon="target" label="Pression min" :value="records.pressure_min.value" unit="hPa" :sub="formatDate(records.pressure_min.timestamp)" />
          <StatCard icon="wind" label="Vent max" :value="records.wind_speed_max.value" unit="km/h" :sub="formatDate(records.wind_speed_max.timestamp)" />
        </div>
      </section>

      <section class="section">
        <h2>Profil saisonnier (température par mois)</h2>
        <p class="section-note">
          Moyenne, minimum et maximum observés chaque mois depuis le début de la collecte. Les
          maximums peuvent être surestimés l'été : le capteur chauffe au soleil en journée.
        </p>
        <div class="chart-box">
          <Line :data="climatologyChart" :options="climatologyOptions" />
        </div>
      </section>

      <section class="section">
        <h2>Comparaison année sur année</h2>
        <p v-if="yearsAvailable.length < 2" class="section-note callout">
          Historique encore trop court pour une vraie comparaison d'une année sur l'autre
          (il faut au moins deux années qui se chevauchent). La courbe ci-dessous montre déjà
          le profil de {{ yearsAvailable[0] ?? 'cette année' }} — la comparaison deviendra possible
          au fil du temps.
        </p>
        <div class="chart-box">
          <Line :data="yearlyChart" :options="yearlyOptions" />
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.intro {
  color: var(--color-text-muted);
  margin-top: 0.25rem;
  margin-bottom: 2rem;
}

.section {
  margin-bottom: 2.5rem;
}

.section h2 {
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}

.section-note {
  color: var(--color-text-muted);
  font-size: 0.88rem;
  margin-bottom: 1rem;
}

.callout {
  background: var(--color-accent-soft);
  color: var(--color-text);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
}

.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}

.record-caveat {
  display: flex;
  align-items: flex-start;
  gap: 0.35rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-warning-text);
  background: var(--color-warning-bg);
  border-radius: 6px;
  padding: 0.4rem 0.5rem;
  line-height: 1.35;
}

.record-caveat svg {
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.chart-box {
  height: 320px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.loading {
  color: var(--color-text-muted);
  padding: 3rem 0;
}
</style>
