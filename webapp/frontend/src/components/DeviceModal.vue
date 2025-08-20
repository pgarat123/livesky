<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';

const props = defineProps({
  show: Boolean,
  device: Object, // null for 'add' mode, device object for 'edit' mode
});

const emit = defineEmits(['close', 'save']);

const formData = ref({ device_name: '', location_name: '' });

// Watch for the device prop to change and update the form
watch(() => props.device, (newDevice) => {
  if (newDevice) {
    formData.value = {
      device_name: newDevice.device_name,
      location_name: newDevice.location_name
    };
  } else {
    // Reset for 'add' mode
    formData.value = { device_name: '', location_name: '' };
  }
});

const saveChanges = () => {
  emit('save', formData.value);
};

const closeModal = () => {
  emit('close');
};
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <div class="modal-header">
        <h2>{{ device ? 'Modifier l\'appareil' : 'Ajouter un appareil' }}</h2>
        <button @click="closeModal" class="close-button">&times;</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="saveChanges">
          <div class="form-group">
            <label for="device-name">Nom de l'appareil</label>
            <input type="text" id="device-name" v-model="formData.device_name" required>
          </div>
          <div class="form-group">
            <label for="location-name">Nom de l'emplacement</label>
            <input type="text" id="location-name" v-model="formData.location_name" required>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button @click="closeModal" class="btn btn-secondary">Annuler</button>
        <button @click="saveChanges" class="btn btn-primary">Enregistrer</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  transition: opacity 0.3s ease;
}

.modal-container {
  background: var(--color-background-soft);
  color: var(--color-text);
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  width: 90%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  margin: 0;
  color: var(--color-heading);
}

.close-button {
  border: none;
  background: transparent;
  font-size: 2rem;
  cursor: pointer;
  color: var(--color-text);
  opacity: 0.7;
}
.close-button:hover {
  opacity: 1;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--color-text);
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-background);
  color: var(--color-text);
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-border-hover);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  background-color: var(--color-background-mute);
}

.btn {
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s ease;
}

.btn-primary {
  background-color: #007bff;
  color: var(--vt-c-white);
}
.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: var(--vt-c-white);
}
.btn-secondary:hover {
  background-color: #545b62;
}
</style>
