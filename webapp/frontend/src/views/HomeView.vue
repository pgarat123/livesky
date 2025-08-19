<script setup>
import { ref, onMounted } from 'vue'

const sensorData = ref([])

onMounted(async () => {
  try {
    const response = await fetch('http://192.168.1.20:5001/api/data')
    
    const data = await response.json()
    
    sensorData.value = data
  } catch (error) {
    console.error('Erreur lors de la récupération des données:', error)
  }
})
</script>

<template>
  <main>
    <h1>Données de la station météo</h1>
    
    <div v-if="sensorData.length > 0">
      <table>
        <thead>
          <tr>
            <th>Température</th>
            <th>Humidité</th>
            <th>Horodatage</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="data in sensorData" :key="data.id">
            <td>{{ data.temperature }} °C</td>
            <td>{{ data.humidity }} %</td>
            <td>{{ data.timestamp }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>
      <p>Chargement des données...</p>
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
</style>