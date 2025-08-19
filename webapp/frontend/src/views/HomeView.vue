<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import VueFeather from 'vue-feather';

const sensorData = ref([])
const API_BASE_URL = 'http://192.168.1.20:5001' // Temp not fixed IP
let pollingInterval = null

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
  pollingInterval = setInterval(fetchData, 10000) // Rafraîchit toutes les 10 secondes
})

onUnmounted(() => {
  clearInterval(pollingInterval) // Nettoyage de l'intervalle à la destruction du composant
})
</script>

<template>
  <main>
    <h1>Tableau de Bord Météo</h1>

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
              <span>{{ reading.temperature }} °C</span>
            </li>
            <li v-if="reading.humidity !== null">
              <span class="data-point">
                <vue-feather type="droplet" size="16"></vue-feather>
                <span>Humidité:</span>
              </span>
              <span>{{ reading.humidity }} %</span>
            </li>
            <li v-if="reading.pressure !== null">
               <span class="data-point">
                <vue-feather type="activity" size="16"></vue-feather>
                <span>Pression:</span>
              </span>
              <span>{{ reading.pressure }} hPa</span>
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
}

.device-card {
  text-decoration: none;
  color: inherit;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  background-color: #f9f9f9;
}

.card-header {
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.card-header p {
  margin: 0;
  color: #666;
}

.card-body .timestamp {
  font-size: 0.8em;
  color: #888;
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
  border-bottom: 1px solid #eee;
}

.card-body li:last-child {
  border-bottom: none;
}

.data-point {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
