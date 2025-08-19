<script setup>
import { ref, onMounted } from 'vue';

const devices = ref([]);
const API_BASE_URL = 'http://192.168.1.20:5001'; // Temp IP

const fetchDevices = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/devices`);
    if (!response.ok) {
      throw new Error('Failed to fetch devices');
    }
    devices.value = await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération des appareils:', error);
  }
};

onMounted(() => {
  fetchDevices();
});

const handleAdd = () => {
  alert('Logique d\'ajout à implémenter');
};

const handleEdit = (id) => {
  alert(`Logique de modification à implémenter pour l\'appareil ${id}`);
};

const handleDelete = (id) => {
  alert(`Logique de suppression à implémenter pour l\'appareil ${id}`);
};
</script>

<template>
  <main>
    <div class="header">
      <h1>Administration des Appareils</h1>
      <button @click="handleAdd" class="btn btn-primary">Ajouter un appareil</button>
    </div>

    <table class="devices-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Nom de l\'appareil</th>
          <th>Emplacement</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="devices.length === 0">
          <td colspan="4" class="empty-state">Aucun appareil trouvé.</td>
        </tr>
        <tr v-for="device in devices" :key="device.device_id">
          <td>{{ device.device_id }}</td>
          <td>{{ device.device_name }}</td>
          <td>{{ device.location_name }}</td>
          <td class="actions">
            <button @click="handleEdit(device.device_id)" class="btn btn-secondary">Modifier</button>
            <button @click="handleDelete(device.device_id)" class="btn btn-danger">Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.devices-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.devices-table th, .devices-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.devices-table thead {
  background-color: #f9f9f9;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #888;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}
</style>
