<script setup>
import { ref, onMounted } from 'vue';
import DeviceModal from '../components/DeviceModal.vue';

const devices = ref([]);
const API_BASE_URL = 'http://192.168.1.20:5001'; // Temp IP

const showModal = ref(false);
const editingDevice = ref(null);

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

const openAddModal = () => {
  editingDevice.value = null;
  showModal.value = true;
};

const openEditModal = (device) => {
  editingDevice.value = { ...device }; // Create a copy to avoid modifying the list directly
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const handleSave = async (formData) => {
  const isEditMode = !!editingDevice.value;
  const url = isEditMode
    ? `${API_BASE_URL}/api/devices/${editingDevice.value.device_id}`
    : `${API_BASE_URL}/api/devices`;

  const method = isEditMode ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      throw new Error('Failed to save device');
    }

    await fetchDevices(); // Refresh the list
    closeModal();
  } catch (error) {
    console.error('Erreur lors de l\'enregistrement de l\'appareil:', error);
  }
};

const handleDelete = async (deviceId) => {
  if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet appareil et toutes ses données associées ?')) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete device');
    }

    await fetchDevices(); // Refresh the list
  } catch (error) {
    console.error(`Erreur lors de la suppression de l\'appareil ${deviceId}:`, error);
  }
};
</script>

<template>
  <main>
    <div class="header">
      <h1>Administration des Appareils</h1>
      <button @click="openAddModal" class="btn btn-primary">Ajouter un appareil</button>
    </div>

    <table class="devices-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Nom de l'appareil</th>
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
            <button @click="openEditModal(device)" class="btn btn-secondary">Modifier</button>
            <button @click="handleDelete(device.device_id)" class="btn btn-danger">Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>

    <DeviceModal
      :show="showModal"
      :device="editingDevice"
      @close="closeModal"
      @save="handleSave"
    />
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
  background-color: var(--color-background-soft);
}

.devices-table th, .devices-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.devices-table th {
  color: var(--color-heading);
}

.devices-table tbody tr:last-of-type td {
  border-bottom: none;
}

.devices-table thead {
  background-color: var(--color-background-mute);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text);
  opacity: 0.7;
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
  color: var(--vt-c-white); /* Assuming buttons always have light text */
}

.btn-primary {
  background-color: #007bff;
}

.btn-secondary {
  background-color: #6c757d;
}

.btn-danger {
  background-color: #dc3545;
}
</style>
