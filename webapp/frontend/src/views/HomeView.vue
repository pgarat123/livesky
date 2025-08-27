<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import VueFeather from 'vue-feather';

const sensorData = ref([])
const showDisclaimer = ref(false)
const API_BASE_URL = 'http://192.168.1.20:5001' // Temp not fixed IP
let pollingInterval = null
let timeInterval = null

const checkDisclaimerTime = () => {
  const currentHour = new Date().getHours();
  showDisclaimer.value = currentHour >= 9 && currentHour < 18;
};

const fetchData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/data`)
    sensorData.value = await response.json()
  } catch (error) {
    console.error('Erreur lors de la récupération des données:', error)
    // Optionnel : vous pourriez vouloir arrêter le polling en cas d'erreur réseau persistante
    // clearInterval(pollingInterval)
  }
}

onMounted(() => {
  fetchData() // Premier chargement immédiat
  checkDisclaimerTime() // Vérifie l'heure au montage
  pollingInterval = setInterval(fetchData, 10000) // Rafraîchit toutes les 10 secondes
  timeInterval = setInterval(checkDisclaimerTime, 60000) // Vérifie l'heure chaque minute
})

onUnmounted(() => {
  clearInterval(pollingInterval) // Nettoyage de l'intervalle à la destruction du composant
  clearInterval(timeInterval)
})

const getTrendIcon = (trend) => {
  if (trend === 'rising') return 'arrow-up';
  if (trend === 'falling') return 'arrow-down';
  return 'minus';
};

const getTrendColor = (trend) => {
  if (trend === 'rising') return 'color: #4ade80;'; // green-400
  if (trend === 'falling') return 'color: #f87171;'; // red-400
  return 'color: #9ca3af;'; // gray-400
}

const getWeatherInterpretation = (reading) => {
  if (!reading) return null;

  const { temperature, humidity, trends } = reading;
  let icon = 'sun';
  let condition = 'Ensoleillé';
  let forecast = 'Le temps semble stable.';

  // --- Logique de condition actuelle ---
  if (temperature !== null && temperature <= 0.5 && humidity !== null && humidity > 85) {
    condition = 'Neige possible';
    icon = 'cloud-snow';
  } else if (humidity !== null && humidity > 90) {
    condition = 'Averses possibles';
    icon = 'cloud-rain';
  } else if (humidity !== null && humidity > 75) {
    condition = 'Très nuageux';
    icon = 'cloud';
  } else if (humidity !== null && humidity > 60) {
    condition = 'Partiellement nuageux';
    icon = 'cloud';
  }

  if (trends) {
    if (trends.pressure === 'falling') {
      forecast = 'La pression chute, le temps pourrait se dégrader.';
    } else if (trends.pressure === 'rising') {
      forecast = 'La pression monte, une amélioration est probable.';
    } else if (trends.humidity === 'rising' && trends.temperature === 'falling') {
      forecast = 'Le temps devient plus froid et humide.';
    }
  }

  return { icon, condition, forecast };
};

const weatherInterpretation = computed(() => {
  if (!sensorData.value || sensorData.value.length === 0) {
    return null;
  }
  // Basé sur la première station météo pour une vue d'ensemble
  return getWeatherInterpretation(sensorData.value[0]);
});
</script>

<template>
  <main>
    <h1>Tableau de Bord Météo</h1>

    <div class="disclaimer-box" v-if="showDisclaimer">
      <vue-feather type="alert-triangle" size="18"></vue-feather>
      <p><strong>Avertissement :</strong> En journée, la température peut être inexacte et surestimée de 2 degrés ou plus si le capteur est exposé en plein soleil.</p>
    </div>

    <div class="interpretation-container" v-if="weatherInterpretation">
      <div class="current-condition">
        <vue-feather :type="weatherInterpretation.icon" size="48"></vue-feather>
        <p class="condition-text">{{ weatherInterpretation.condition }}</p>
      </div>
      <div class="forecast">
        <vue-feather type="trending-up" size="20"></vue-feather>
        <p>{{ weatherInterpretation.forecast }}</p>
      </div>
    </div>

    <div class="dashboard-container" v-if="sensorData.length > 0">
      <RouterLink :to="`/device/${reading.device_id}`" class="device-card" v-for="reading in sensorData" :key="reading.id">

        <div class="card-header">
          <h2>{{ reading.device_name }}</h2>
          <p>{{ reading.location_name }}</p>
        </div>

        <div class="card-body">
          <p class="timestamp">{{ new Date(reading.timestamp).toLocaleString() }}</p>
          <ul>
            <li v-if="reading.temperature !== null">
              <span class="data-point">
                <vue-feather type="thermometer" size="16"></vue-feather>
                <span>Température:</span>
              </span>
              <span class="value-trend">
                <vue-feather
                  v-if="reading.trends"
                  :type="getTrendIcon(reading.trends.temperature)"
                  size="16"
                  :style="getTrendColor(reading.trends.temperature)"
                ></vue-feather>
                <span>{{ reading.temperature }} °C</span>
              </span>
            </li>
            <li v-if="reading.humidity !== null">
              <span class="data-point">
                <vue-feather type="droplet" size="16"></vue-feather>
                <span>Humidité:</span>
              </span>
              <span class="value-trend">
                <vue-feather
                  v-if="reading.trends"
                  :type="getTrendIcon(reading.trends.humidity)"
                  size="16"
                  :style="getTrendColor(reading.trends.humidity)"
                ></vue-feather>
                <span>{{ reading.humidity }} %</span>
              </span>
            </li>
            <li v-if="reading.pressure !== null">
               <span class="data-point">
                <vue-feather type="target" size="16"></vue-feather>
                <span>Pression:</span>
              </span>
              <span class="value-trend">
                <vue-feather
                  v-if="reading.trends"
                  :type="getTrendIcon(reading.trends.pressure)"
                  size="16"
                  :style="getTrendColor(reading.trends.pressure)"
                ></vue-feather>
                <span>{{ reading.pressure }} hPa</span>
              </span>
            </li>
            <li v-if="reading.wind_speed !== null">
              <span class="data-point">
                <vue-feather type="wind" size="16"></vue-feather>
                <span>Vitesse du vent:</span>
              </span>
              <span>{{ reading.wind_speed }} km/h</span>
            </li>
            <li v-if="reading.wind_direction !== null">
              <span class="data-point">
                <vue-feather type="compass" size="16"></vue-feather>
                <span>Direction du vent:</span>
              </span>
              <span>{{ reading.wind_direction }}</span>
            </li>
          </ul>
        </div>
        <div class="additional-data-section">
          <hr class="section-separator">
          <ul>
            <li v-if="reading.heat_index !== null">
              <span class="data-point">
                <vue-feather type="thermometer" size="16"></vue-feather>
                <span>Indice de chaleur:</span>
              </span>
              <span>{{ reading.heat_index }} °C</span>
            </li>
            <li v-if="reading.wind_chill !== null">
              <span class="data-point">
                <vue-feather type="wind" size="16"></vue-feather>
                <span>Temp. ressentie:</span>
              </span>
              <span>{{ reading.wind_chill }} °C</span>
            </li>
          </ul>
        </div>
      </RouterLink>
    </div>



    <div v-else>
      <p>Chargement des données ou aucune donnée disponible...</p>
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
}

.dashboard-container {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  justify-content: center; /* Center cards horizontally */
}

.device-card {
  text-decoration: none;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  background-color: var(--color-background-soft);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  flex-grow: 1; /* Allow cards to grow */
  max-width: 400px; /* But not too wide */
  transition: border-color 0.3s, background-color 0.3s;
}

.device-card:hover {
  border-color: var(--color-border-hover);
}

.card-header {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.card-header h2 {
  margin: 0;
  color: var(--color-heading);
}

.card-header p {
  margin: 0;
  color: var(--color-text);
}

.card-body .timestamp {
  font-size: 0.8em;
  color: var(--color-text);
  opacity: 0.8;
  margin-bottom: 1rem;
}

.card-body ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.card-body li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border);
}

.card-body li:last-child {
  border-bottom: none;
}

.additional-data-section {
  margin-top: 1rem;
  padding-top: 1rem;
}

.section-separator {
  border: 0;
  height: 1px;
  background-image: linear-gradient(to right, rgba(0, 0, 0, 0), var(--color-border), rgba(0, 0, 0, 0));
  margin-bottom: 1rem;
}

.data-point {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.value-trend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Stacking on mobile */
@media (max-width: 768px) {
  .dashboard-container {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .device-card {
    width: 100%;
    max-width: 450px; /* Adjust max-width for mobile if needed */
  }

  .interpretation-container {
    flex-direction: column;
    align-items: flex-start;
    gap: 1.5rem;
    padding: 1rem;
  }

  .current-condition {
    gap: 1rem;
  }

  .current-condition .condition-text {
    font-size: 1.5em;
  }

  .forecast {
    font-size: 1em;
  }

  /* Prevents the icons from shrinking when space is limited */
  .current-condition .vue-feather,
  .forecast .vue-feather {
    flex-shrink: 0;
  }
}

.disclaimer-box {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: #fef9c3; /* A light yellow color */
  border: 1px solid #fde047; /* A darker yellow border */
  color: #713f12; /* Dark text for readability */
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

/* Prevents the icon from shrinking and being cut off on mobile */
.disclaimer-box .vue-feather {
  flex-shrink: 0;
}

.disclaimer-box p {
  margin: 0;
}

.interpretation-container {
  background-color: var(--color-background-mute);
  border-radius: 8px;
  padding: 1.5rem 2rem;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.current-condition {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.current-condition .condition-text {
  font-size: 1.8em;
  font-weight: 600;
  color: var(--color-heading);
  margin: 0;
}

.forecast {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.1em;
  color: var(--color-text);
  opacity: 0.9;
}

.forecast p {
  margin: 0;
}

</style>
