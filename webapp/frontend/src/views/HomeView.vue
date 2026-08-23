<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import VueFeather from 'vue-feather'
import StatCard from '../components/StatCard.vue'
import Sparkline from '../components/Sparkline.vue'
import SunBadge from '../components/SunBadge.vue'

const sensorData = ref([])
const sparklines = ref({}) // { [device_id]: { temperature: {labels,data}, humidity: {...}, pressure: {...} } }
const now = ref(new Date())
let pollingInterval = null
let sparklineInterval = null
let clockInterval = null

// Cadence normale de la station : environ une mesure toutes les 5 à 8 min.
// Au-delà de 2h sans nouvelle mesure, il y a probablement un vrai souci
// (coupure secteur, WiFi, capteur en panne) plutôt qu'un simple raté ponctuel.
const STALE_AFTER_MIN = 20
const OFFLINE_AFTER_MIN = 120
const FROST_RISK_C = 2

const fetchData = async () => {
  try {
    const response = await fetch('/api/data')
    sensorData.value = await response.json()
  } catch (error) {
    console.error('Erreur lors de la récupération des données:', error)
  }
}

const SPARK_SENSORS = ['temperature', 'humidity', 'pressure']

const fetchSparklines = async () => {
  for (const device of sensorData.value) {
    const perSensor = {}
    for (const sensor of SPARK_SENSORS) {
      try {
        const res = await fetch(`/api/devices/${device.device_id}/history?sensor=${sensor}&range=6`)
        perSensor[sensor] = await res.json()
      } catch (error) {
        console.error(`Erreur sparkline ${sensor}:`, error)
      }
    }
    sparklines.value = { ...sparklines.value, [device.device_id]: perSensor }
  }
}

onMounted(async () => {
  await fetchData()
  fetchSparklines()
  pollingInterval = setInterval(fetchData, 10000)
  sparklineInterval = setInterval(fetchSparklines, 5 * 60 * 1000)
  clockInterval = setInterval(() => { now.value = new Date() }, 30000)
})

onUnmounted(() => {
  clearInterval(pollingInterval)
  clearInterval(sparklineInterval)
  clearInterval(clockInterval)
})

const getTrendIcon = (trend) => {
  if (trend === 'rising') return 'arrow-up'
  if (trend === 'falling') return 'arrow-down'
  return 'minus'
}

const getTrendStyle = (trend) => {
  if (trend === 'rising') return { color: 'var(--color-rising)' }
  if (trend === 'falling') return { color: 'var(--color-falling)' }
  return { color: 'var(--color-stable)' }
}

const getCondition = (reading) => {
  const { humidity, temperature } = reading
  if (temperature !== null && temperature <= 0.5 && humidity !== null && humidity > 85) {
    return { icon: 'cloud-snow', text: 'Neige possible' }
  }
  if (humidity !== null && humidity > 90) {
    return { icon: 'cloud-rain', text: 'Averses possibles' }
  }
  if (humidity !== null && humidity > 75) {
    return { icon: 'cloud', text: 'Très nuageux' }
  }
  if (humidity !== null && humidity > 60) {
    return { icon: 'cloud', text: 'Partiellement nuageux' }
  }
  return { icon: 'sun', text: 'Ciel dégagé' }
}

const spark = (deviceId, sensor) => {
  const d = sparklines.value[deviceId]?.[sensor]
  return { labels: d?.labels ?? [], data: d?.data ?? [] }
}

const formattedTime = (ts) => new Date(ts).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })

const freshness = (reading) => {
  const minutes = Math.max(0, Math.round((now.value - new Date(reading.timestamp)) / 60000))
  const status = minutes < STALE_AFTER_MIN ? 'fresh' : minutes < OFFLINE_AFTER_MIN ? 'stale' : 'offline'
  return { status, minutes }
}

const formatRelative = (minutes) => {
  if (minutes < 1) return "à l'instant"
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return `il y a ${hours}h${rest > 0 ? String(rest).padStart(2, '0') : ''}`
}

const isFrostRisk = (reading) => reading.temperature !== null && reading.temperature <= FROST_RISK_C
</script>

<template>
  <main class="page">
    <div v-if="sensorData.length > 0" class="devices">
      <section v-for="reading in sensorData" :key="reading.id" class="device-block">
        <div class="hero card">
          <div class="hero-main">
            <vue-feather :type="getCondition(reading).icon" size="40"></vue-feather>
            <div>
              <h1>{{ getCondition(reading).text }}</h1>
              <p class="location">{{ reading.device_name }} · {{ reading.location_name }}</p>
            </div>
          </div>
          <div class="hero-meta">
            <SunBadge
              v-if="reading.sun"
              :risk="reading.sun.exposure_risk"
              :corrected-temperature="reading.sun.temperature_corrected"
            />
            <div class="freshness" :class="freshness(reading).status" :title="formattedTime(reading.timestamp)">
              <span class="dot"></span>
              <span>{{ formatRelative(freshness(reading).minutes) }}</span>
            </div>
          </div>
        </div>

        <div v-if="freshness(reading).status === 'offline'" class="alert-banner offline-banner">
          <vue-feather type="wifi-off" size="18"></vue-feather>
          <p>
            Dernière mesure reçue {{ formatRelative(freshness(reading).minutes) }} ({{ formattedTime(reading.timestamp) }}) —
            la station ne répond peut-être plus (coupure secteur, WiFi, ou capteur).
          </p>
        </div>

        <div v-if="isFrostRisk(reading)" class="alert-banner frost-banner">
          <vue-feather type="cloud-snow" size="18"></vue-feather>
          <p><strong>Risque de gel</strong> — pensez aux plantes sensibles et aux canalisations extérieures.</p>
        </div>

        <div class="stats-grid">
          <StatCard icon="thermometer" label="Température" :value="reading.temperature" unit="°C" v-if="reading.temperature !== null">
            <vue-feather :type="getTrendIcon(reading.trends?.temperature)" size="15" :style="getTrendStyle(reading.trends?.temperature)"></vue-feather>
            <template #footer>
              <Sparkline v-bind="spark(reading.device_id, 'temperature')" color="#dc6803" />
            </template>
          </StatCard>

          <StatCard icon="droplet" label="Humidité" :value="reading.humidity" unit="%" v-if="reading.humidity !== null">
            <vue-feather :type="getTrendIcon(reading.trends?.humidity)" size="15" :style="getTrendStyle(reading.trends?.humidity)"></vue-feather>
            <template #footer>
              <Sparkline v-bind="spark(reading.device_id, 'humidity')" color="#2f7fd6" />
            </template>
          </StatCard>

          <StatCard icon="target" label="Pression" :value="reading.pressure" unit="hPa" v-if="reading.pressure !== null">
            <vue-feather :type="getTrendIcon(reading.trends?.pressure)" size="15" :style="getTrendStyle(reading.trends?.pressure)"></vue-feather>
            <template #footer>
              <Sparkline v-bind="spark(reading.device_id, 'pressure')" color="#7c3aed" />
            </template>
          </StatCard>

          <StatCard icon="wind" label="Vent" :value="reading.wind_speed" unit="km/h" :sub="reading.wind_direction" v-if="reading.wind_speed !== null" />

          <StatCard icon="thermometer" label="Ressenti" :value="reading.heat_index ?? reading.wind_chill" unit="°C" v-if="reading.heat_index !== null || reading.wind_chill !== null" />
        </div>

        <RouterLink :to="`/device/${reading.device_id}`" class="detail-link">
          Voir l'historique détaillé
          <vue-feather type="arrow-right" size="15"></vue-feather>
        </RouterLink>
      </section>
    </div>

    <div v-else class="loading">
      <p>Chargement des données…</p>
    </div>
  </main>
</template>

<style scoped>
.devices {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.5rem 1.75rem;
  margin-bottom: 1.25rem;
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.hero-main h1 {
  font-size: 1.4rem;
}

.location {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-top: 0.15rem;
}

.hero-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.freshness {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.freshness .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
  flex-shrink: 0;
}

.freshness.stale .dot {
  background: var(--color-rising);
}

.freshness.offline .dot {
  background: var(--color-danger);
}

.freshness.offline {
  color: var(--color-danger);
  font-weight: 600;
}

.alert-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1.25rem;
  font-size: 0.88rem;
}

.alert-banner svg {
  flex-shrink: 0;
}

.alert-banner p {
  margin: 0;
}

.offline-banner {
  background: #fde8e8;
  border: 1px solid #f5b8b8;
  color: #7a1f1f;
}

:root[data-theme='dark'] .offline-banner {
  background: #3a1c1c;
  border-color: #6b2b2b;
  color: #f3b4b4;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) .offline-banner {
    background: #3a1c1c;
    border-color: #6b2b2b;
    color: #f3b4b4;
  }
}

.frost-banner {
  background: var(--color-accent-soft);
  border: 1px solid var(--color-accent);
  color: var(--color-text);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.stats-grid :deep(.value-row) {
  flex-wrap: wrap;
}

.stats-grid :deep(.sparkline) {
  margin-top: 0.6rem;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1.25rem;
  color: var(--color-accent);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.loading {
  color: var(--color-text-muted);
  padding: 3rem 0;
  text-align: center;
}

@media (max-width: 640px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-meta {
    align-items: flex-start;
  }
}
</style>
