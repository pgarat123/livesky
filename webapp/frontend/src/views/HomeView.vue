<script setup>
import { ref, onMounted } from 'vue'

const sensorData = ref([])
const API_BASE_URL = 'http://192.168.1.20:5001' // Temp not fixed IP

onMounted(async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/data`)
    sensorData.value = await response.json()
  } catch (error) {
    console.error('Erreur lors de la récupération des données:', error)
  }
})
</script>

<template>
  <main>
    <h1>Tableau de Bord Météo</h1>

    <div class="dashboard-container" v-if="sensorData.length > 0">
      <div class="device-card" v-for="reading in sensorData" :key="reading.id">

        <div class="card-header">
          <h2>{{ reading.device_name }}</h2>
          <p>{{ reading.location_name }}</p>
        </div>

        <div class="card-body">
          <p class="timestamp">{{ new Date(reading.timestamp).toLocaleString() }}</p>
          <ul>
            <li v-if="reading.temperature !== null">
              <span>🌡️ Température:</span>
              <span>{{ reading.temperature }} °C</span>
            </li>
            <li v-if="reading.humidity !== null">
              <span>💧 Humidité:</span>
              <span>{{ reading.humidity }} %</span>
            </li>
            <li v-if="reading.pressure !== null">
              <span>🌬️ Pression:</span>
              <span>{{ reading.pressure }} hPa</span>
            </li>
            <li v-if="reading.wind_speed !== null">
              <span>💨 Vitesse du vent:</span>
              <span>{{ reading.wind_speed }} km/h</span>
            </li>
            <li v-if="reading.wind_direction !== null">
              <span>🧭 Direction du vent:</span>
              <span>{{ reading.wind_direction }}</span>
            </li>
          </ul>
        </div>
      </div>
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
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.card-body li:last-child {
  border-bottom: none;
}
</style>
