<script setup>
import { ref, onMounted, computed } from 'vue'
import VueFeather from 'vue-feather'

const loading = ref(true)
const forecast = ref(null)
const showMethod = ref(false)

const REASON_MESSAGES = {
  no_data: "Aucune donnée pour cet appareil pour l'instant.",
  no_recent_data: "Pas de mesure de pression assez récente pour calculer une tendance.",
  not_enough_analogs: "Pas assez de situations comparables dans l'historique pour cette combinaison de tendance et de période de l'année.",
}

const load = async () => {
  loading.value = true
  try {
    const devicesRes = await fetch('/api/devices')
    const devices = await devicesRes.json()
    const deviceId = devices[0]?.device_id
    if (!deviceId) return
    const res = await fetch(`/api/forecast/${deviceId}`)
    forecast.value = await res.json()
  } catch (error) {
    console.error('Erreur lors du chargement de la prévision:', error)
  } finally {
    loading.value = false
  }
}

onMounted(load)

const trendIcon = computed(() => {
  const t = forecast.value?.pressure_trend_3h_hpa
  if (t === undefined || t === null) return 'minus'
  if (t <= -0.5) return 'arrow-down'
  if (t >= 0.5) return 'arrow-up'
  return 'minus'
})

const confidenceLabel = computed(() => {
  const c = forecast.value?.confidence
  if (c === 'moyenne') return { text: 'Confiance moyenne', class: 'confidence-medium' }
  return { text: 'Confiance faible', class: 'confidence-low' }
})
</script>

<template>
  <main class="page">
    <h1>Prévisions</h1>
    <p class="intro">
      Pas de modèle météo complexe ici : une simple lecture de la tendance de pression récente,
      confrontée à ce qui s'est historiquement passé dans des situations similaires mesurées par
      <strong>cette station</strong>.
    </p>

    <div v-if="loading" class="loading">Chargement…</div>

    <template v-else-if="forecast?.available">
      <div class="forecast-card card">
        <div class="trend-row">
          <vue-feather :type="trendIcon" size="28"></vue-feather>
          <div>
            <p class="trend-value">{{ forecast.pressure_trend_3h_hpa >= 0 ? '+' : '' }}{{ forecast.pressure_trend_3h_hpa }} hPa <span class="muted">/ 3h</span></p>
            <p class="muted">Pression actuelle : {{ forecast.current_pressure }} hPa</p>
          </div>
          <span class="confidence-badge" :class="confidenceLabel.class">{{ confidenceLabel.text }}</span>
        </div>

        <p class="forecast-text">{{ forecast.forecast_text }}</p>

        <p class="analog-count">
          Basé sur {{ forecast.analog_count }} situations historiques comparables trouvées dans les
          données de la station.
        </p>

        <button class="method-toggle" @click="showMethod = !showMethod">
          <vue-feather :type="showMethod ? 'chevron-up' : 'chevron-down'" size="16"></vue-feather>
          Comment ça marche, et ce que ça ne vaut pas
        </button>

        <div v-if="showMethod" class="method-panel">
          <p>{{ forecast.method }}</p>
          <ul>
            <li v-for="(limit, i) in forecast.limitations" :key="i">{{ limit }}</li>
          </ul>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="empty-card card">
        <vue-feather type="clock" size="28"></vue-feather>
        <p>{{ REASON_MESSAGES[forecast?.reason] ?? "Prévision indisponible pour le moment." }}</p>
        <p v-if="forecast?.analog_count !== undefined" class="muted">
          {{ forecast.analog_count }} situation(s) comparable(s) trouvée(s) pour l'instant (il en faut au moins 15).
          Ça s'améliore au fur et à mesure que la station accumule de l'historique.
        </p>
      </div>
    </template>
  </main>
</template>

<style scoped>
.intro {
  color: var(--color-text-muted);
  margin: 0.5rem 0 2rem;
  max-width: 60ch;
}

.forecast-card, .empty-card {
  padding: 1.5rem 1.75rem;
}

.trend-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.trend-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-heading);
}

.muted {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 400;
}

.confidence-badge {
  margin-left: auto;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.confidence-medium {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.confidence-low {
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}

.forecast-text {
  font-size: 1.02rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.analog-count {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
}

.method-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  color: var(--color-accent);
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0.3rem 0;
}

.method-panel {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.88rem;
  line-height: 1.6;
}

.method-panel ul {
  margin-top: 0.5rem;
  padding-left: 1.2rem;
}

.method-panel li {
  margin-bottom: 0.35rem;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.6rem;
  color: var(--color-text-muted);
}

.loading {
  color: var(--color-text-muted);
  padding: 3rem 0;
}
</style>
