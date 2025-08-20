<script setup>
import { ref, onMounted, watch } from 'vue';
import DeviceModal from '../components/DeviceModal.vue';

// Refs for data
const devices = ref([]);
const allReadings = ref([]);
const deviceReadings = ref([]);

// Refs for state management
const API_BASE_URL = 'http://192.168.1.20:5001'; // Temp
const showModal = ref(false);
const editingDevice = ref(null);
const selectedDevice = ref(null);
const readingsLimit = ref(50);
const globalReadingsLimit = ref(50);

// --- API Functions ---

const fetchDevices = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/devices`);
    if (!response.ok) throw new Error('Failed to fetch devices');
    devices.value = await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération des appareils:', error);
  }
};

const fetchAllReadings = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/admin/readings?limit=${globalReadingsLimit.value}`);
    if (!response.ok) throw new Error('Failed to fetch all readings');
    allReadings.value = await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération de toutes les données:', error);
  }
};

const fetchDeviceReadings = async () => {
  if (!selectedDevice.value) return;
  try {
    const url = `${API_BASE_URL}/api/admin/devices/${selectedDevice.value.device_id}/readings?limit=${readingsLimit.value}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch device readings');
    deviceReadings.value = await response.json();
  } catch (error) {
    console.error(`Erreur lors de la récupération des données pour l'appareil ${selectedDevice.value.device_id}:`, error);
  }
};

// --- Device CRUD Handlers ---

const handleSaveDevice = async (formData) => {
  const isEditMode = !!editingDevice.value;
  const url = isEditMode
    ? `${API_BASE_URL}/api/devices/${editingDevice.value.device_id}`
    : `${API_BASE_URL}/api/devices`;
  const method = isEditMode ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    if (!response.ok) throw new Error('Failed to save device');
    await fetchDevices();
    closeModal();
  } catch (error) {
    console.error('Erreur lors de l\'enregistrement de l\'appareil:', error);
  }
};

const handleDeleteDevice = async (deviceId) => {
  if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet appareil et toutes ses données associées ?')) return;

  try {
    const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete device');
    await fetchDevices();
    if (selectedDevice.value && selectedDevice.value.device_id === deviceId) {
      selectedDevice.value = null;
      deviceReadings.value = [];
    }
  } catch (error) {
    console.error(`Erreur lors de la suppression de l'appareil ${deviceId}:`, error);
  }
};

const handleDeleteReading = async (readingId) => {
  if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette lecture ?')) return;

  try {
    const response = await fetch(`${API_BASE_URL}/api/admin/readings/${readingId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete reading');
    // Refresh both lists as the reading could be in either
    await fetchAllReadings();
    if (selectedDevice.value) {
      await fetchDeviceReadings();
    }
  } catch (error) {
    console.error(`Erreur lors de la suppression de la lecture ${readingId}:`, error);
  }
};

// --- Modal Management ---

const openAddModal = () => {
  editingDevice.value = null;
  showModal.value = true;
};

const openEditModal = (device) => {
  editingDevice.value = { ...device };
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

// --- UI Triggers ---

const selectDevice = (device) => {
  selectedDevice.value = device;
  fetchDeviceReadings();
};

// --- Lifecycle and Watchers ---

onMounted(() => {
  fetchDevices();
  fetchAllReadings();
});

watch(readingsLimit, fetchDeviceReadings);
watch(globalReadingsLimit, fetchAllReadings);

const formatTimestamp = (ts) => new Date(ts).toLocaleString();

</script>

<template>
  <main>
    <!-- Devices Section -->
    <div class="header">
      <h1><i class="fas fa-server"></i> Administration des Appareils</h1>
      <button @click="openAddModal" class="btn btn-primary"><i class="fas fa-plus"></i> Ajouter un appareil</button>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Nom</th>
          <th>Emplacement</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="devices.length === 0">
          <td colspan="4" class="empty-state">Aucun appareil trouvé.</td>
        </tr>
        <tr v-for="device in devices" :key="device.device_id" :class="{ 'selected-row': selectedDevice && selectedDevice.device_id === device.device_id }">
          <td>{{ device.device_id }}</td>
          <td>{{ device.device_name }}</td>
          <td>{{ device.location_name }}</td>
          <td class="actions">
            <button @click="selectDevice(device)" class="btn btn-info"><i class="fas fa-eye"></i> Voir Données</button>
            <button @click="openEditModal(device)" class="btn btn-secondary"><i class="fas fa-pencil-alt"></i> Modifier</button>
            <button @click="handleDeleteDevice(device.device_id)" class="btn btn-danger"><i class="fas fa-trash"></i> Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Device-specific Readings Section -->
    <div v-if="selectedDevice" class="data-section">
      <div class="header">
        <h2><i class="fas fa-chart-line"></i> Données pour : {{ selectedDevice.device_name }}</h2>
        <div class="controls">
          <label for="limit">Afficher les</label>
          <input type="number" v-model.number="readingsLimit" min="1" max="1000" id="limit">
          <span>dernières entrées.</span>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Temp (°C)</th>
            <th>Humidité (%)</th>
            <th>Pression (hPa)</th>
            <th>Vent (km/h)</th>
            <th>Direction</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="deviceReadings.length === 0">
            <td colspan="7" class="empty-state">Aucune donnée trouvée pour cet appareil.</td>
          </tr>
          <tr v-for="reading in deviceReadings" :key="reading.id">
            <td>{{ formatTimestamp(reading.timestamp) }}</td>
            <td>{{ reading.temperature }}</td>
            <td>{{ reading.humidity }}</td>
            <td>{{ reading.pressure }}</td>
            <td>{{ reading.wind_speed }}</td>
            <td>{{ reading.wind_direction }}</td>
            <td class="actions">
              <button @click="handleDeleteReading(reading.id)" class="btn btn-danger btn-sm"><i class="fas fa-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- All Readings Section -->
    <div class="data-section">
      <div class="header">
        <h2><i class="fas fa-database"></i> Vue Globale de la Base de Données</h2>
        <div class="controls">
          <label for="global-limit">Afficher les</label>
          <input type="number" v-model.number="globalReadingsLimit" min="1" max="1000" id="global-limit">
          <span>dernières entrées.</span>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Appareil</th>
            <th>Timestamp</th>
            <th>Temp (°C)</th>
            <th>Humidité (%)</th>
            <th>Pression (hPa)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="allReadings.length === 0">
            <td colspan="6" class="empty-state">Aucune donnée trouvée.</td>
          </tr>
          <tr v-for="reading in allReadings" :key="reading.id">
            <td>{{ reading.device_name }} (ID: {{ reading.device_id }})</td>
            <td>{{ formatTimestamp(reading.timestamp) }}</td>
            <td>{{ reading.temperature }}</td>
            <td>{{ reading.humidity }}</td>
            <td>{{ reading.pressure }}</td>
            <td class="actions">
              <button @click="handleDeleteReading(reading.id)" class="btn btn-danger btn-sm"><i class="fas fa-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <DeviceModal :show="showModal" :device="editingDevice" @close="closeModal" @save="handleSaveDevice" />
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header h1, .header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--color-heading);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--color-background-soft);
}

.data-table th, .data-table td {
  padding: 1rem 1.25rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background-color: var(--color-background-mute);
  font-weight: 600;
}

.data-table tbody tr:last-of-type td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background-color: var(--color-background-mute);
}

.selected-row {
  background-color: var(--color-border-hover) !important;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text);
  opacity: 0.7;
}

.actions {
  display: flex;
  align-items: center; /* This will vertically align all items */
  gap: 0.5rem;
}

.btn {
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  color: #fff; /* Assuming buttons always have light text */
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s ease;
}

.btn-sm {
  padding: 0.4rem 0.8rem;
}

.btn-primary {
  background-color: #007bff;
}
.btn-primary:hover { background-color: #0056b3; }

.btn-secondary {
  background-color: #6c757d;
}
.btn-secondary:hover { background-color: #545b62; }

.btn-danger {
  background-color: #dc3545;
}
.btn-danger:hover { background-color: #b02a37; }

.btn-info {
  background-color: #17a2b8;
}
.btn-info:hover { background-color: #117a8b; }

.controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.controls input[type="number"] {
  width: 70px;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
}

/* Font Awesome Icons - assuming it's included globally */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
</style>
