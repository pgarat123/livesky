<script setup>
import { ref, onMounted } from 'vue'
import VueFeather from 'vue-feather'
import ToggleSwitch from '../components/ToggleSwitch.vue'

const deviceId = ref(null)
const subscribers = ref([])
const loading = ref(true)

const newName = ref('')
const newTopic = ref('')
const adding = ref(false)
const addError = ref('')

const testStatus = ref({}) // { [id]: 'sending' | 'ok' | 'error' }

const ALERT_FIELDS = [
  { key: 'frost_enabled', icon: 'cloud-snow', label: 'Risque de gel (≤ 2°C)' },
  { key: 'heatwave_enabled', icon: 'sun', label: 'Chaleur intense (≥ 35°C estimés)' },
  { key: 'high_wind_enabled', icon: 'wind', label: 'Vent fort (≥ 50 km/h)' },
  { key: 'offline_enabled', icon: 'wifi-off', label: 'Station injoignable (2h sans mesure)' },
]

const load = async () => {
  loading.value = true
  try {
    const devicesRes = await fetch('/api/devices')
    const devices = await devicesRes.json()
    deviceId.value = devices[0]?.device_id ?? null
    if (!deviceId.value) return

    const subsRes = await fetch(`/api/notifications/subscribers?device_id=${deviceId.value}`)
    subscribers.value = await subsRes.json()
  } catch (error) {
    console.error('Erreur lors du chargement des abonnés:', error)
  } finally {
    loading.value = false
  }
}

onMounted(load)

const addSubscriber = async () => {
  addError.value = ''
  if (!newName.value.trim() || !newTopic.value.trim()) {
    addError.value = 'Nom et topic ntfy requis.'
    return
  }
  adding.value = true
  try {
    const res = await fetch('/api/notifications/subscribers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.value.trim(), ntfy_topic: newTopic.value.trim(), device_id: deviceId.value }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.error || 'Échec de la création')
    }
    const created = await res.json()
    subscribers.value.push(created)
    newName.value = ''
    newTopic.value = ''
  } catch (error) {
    addError.value = error.message
  } finally {
    adding.value = false
  }
}

const updatePreference = async (sub, field, value) => {
  sub[field] = value // optimistic
  try {
    await fetch(`/api/notifications/subscribers/${sub.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [field]: value }),
    })
  } catch (error) {
    console.error('Erreur lors de la mise à jour:', error)
  }
}

const removeSubscriber = async (sub) => {
  if (!window.confirm(`Supprimer les notifications pour "${sub.name}" ?`)) return
  try {
    await fetch(`/api/notifications/subscribers/${sub.id}`, { method: 'DELETE' })
    subscribers.value = subscribers.value.filter((s) => s.id !== sub.id)
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const sendTest = async (sub) => {
  testStatus.value = { ...testStatus.value, [sub.id]: 'sending' }
  try {
    const res = await fetch(`/api/notifications/subscribers/${sub.id}/test`, { method: 'POST' })
    testStatus.value = { ...testStatus.value, [sub.id]: res.ok ? 'ok' : 'error' }
  } catch (error) {
    testStatus.value = { ...testStatus.value, [sub.id]: 'error' }
  }
  setTimeout(() => {
    testStatus.value = { ...testStatus.value, [sub.id]: null }
  }, 4000)
}
</script>

<template>
  <main class="page">
    <h1>Notifications</h1>
    <p class="intro">
      Reçois une alerte sur ton téléphone en cas de gel, chaleur intense, vent fort ou si la
      station ne répond plus — pas d'appli LiveSky à installer, ça passe par
      <a href="https://ntfy.sh" target="_blank" rel="noopener">ntfy</a>, un service gratuit et
      open-source.
    </p>

    <div class="howto card">
      <h2>Comment s'abonner</h2>
      <ol>
        <li>Installe l'appli <strong>ntfy</strong> (App Store / Google Play), gratuite.</li>
        <li>Choisis un nom de "topic" secret, par ex. <code>livesky-famille-8k2z</code> (n'importe qui connaissant ce nom peut recevoir les mêmes alertes, mieux vaut un nom peu devinable).</li>
        <li>Dans l'appli, abonne-toi à ce topic.</li>
        <li>Ajoute-le ci-dessous avec ce même nom, puis clique sur "Tester" pour vérifier.</li>
      </ol>
    </div>

    <div v-if="loading" class="loading">Chargement…</div>

    <template v-else>
      <div class="subscribers">
        <div v-for="sub in subscribers" :key="sub.id" class="subscriber card">
          <div class="subscriber-header">
            <div>
              <h3>{{ sub.name }}</h3>
              <p class="topic">topic : <code>{{ sub.ntfy_topic }}</code></p>
            </div>
            <div class="subscriber-actions">
              <button class="btn-ghost" @click="sendTest(sub)" :disabled="testStatus[sub.id] === 'sending'">
                {{ testStatus[sub.id] === 'sending' ? 'Envoi…' : testStatus[sub.id] === 'ok' ? 'Envoyé ✓' : testStatus[sub.id] === 'error' ? 'Échec ✗' : 'Tester' }}
              </button>
              <button class="btn-ghost danger" @click="removeSubscriber(sub)">
                <vue-feather type="trash-2" size="15"></vue-feather>
              </button>
            </div>
          </div>
          <div class="toggles">
            <ToggleSwitch
              v-for="field in ALERT_FIELDS"
              :key="field.key"
              :label="field.label"
              :model-value="sub[field.key]"
              @update:model-value="(v) => updatePreference(sub, field.key, v)"
            />
          </div>
        </div>

        <p v-if="subscribers.length === 0" class="empty">Personne n'est encore abonné aux notifications.</p>
      </div>

      <div class="add-form card">
        <h2>Ajouter un abonné</h2>
        <div class="form-row">
          <input v-model="newName" type="text" placeholder="Nom (ex : Maman)" />
          <input v-model="newTopic" type="text" placeholder="Topic ntfy (ex : livesky-famille-8k2z)" />
          <button class="btn-primary" @click="addSubscriber" :disabled="adding">Ajouter</button>
        </div>
        <p v-if="addError" class="error">{{ addError }}</p>
      </div>
    </template>
  </main>
</template>

<style scoped>
.intro {
  color: var(--color-text-muted);
  margin: 0.5rem 0 1.5rem;
  max-width: 65ch;
}

.intro a {
  color: var(--color-accent);
}

.card {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.howto h2 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.howto ol {
  padding-left: 1.2rem;
  color: var(--color-text);
  line-height: 1.7;
}

.howto code {
  background: var(--color-surface-muted);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.88em;
}

.loading {
  color: var(--color-text-muted);
  padding: 2rem 0;
}

.subscribers {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.subscriber-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.subscriber-header h3 {
  font-size: 1.05rem;
}

.topic {
  color: var(--color-text-muted);
  font-size: 0.82rem;
  margin-top: 0.2rem;
}

.subscriber-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.toggles {
  display: flex;
  flex-direction: column;
}

.toggles > *:not(:last-child) {
  border-bottom: 1px solid var(--color-border);
}

.empty {
  color: var(--color-text-muted);
}

.add-form h2 {
  font-size: 1rem;
  margin-bottom: 0.9rem;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.form-row input {
  flex: 1 1 200px;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 0.9rem;
}

.form-row input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin-top: 0.6rem;
}

.btn-primary {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: default;
}

.btn-ghost {
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.btn-ghost:hover {
  background: var(--color-surface-muted);
  color: var(--color-heading);
}

.btn-ghost.danger:hover {
  color: var(--color-danger);
}

@media (max-width: 480px) {
  .subscriber-header {
    flex-direction: column;
  }
}
</style>
