<script setup>
import VueFeather from 'vue-feather'

defineProps({
  icon: { type: String, default: null },
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  unit: { type: String, default: '' },
  sub: { type: String, default: null },
})
</script>

<template>
  <div class="stat-card">
    <div class="stat-header">
      <vue-feather v-if="icon" :type="icon" size="16"></vue-feather>
      <span class="label">{{ label }}</span>
    </div>
    <div class="value-row">
      <span class="value">{{ value }}</span>
      <span v-if="unit" class="unit">{{ unit }}</span>
      <slot></slot>
    </div>
    <div v-if="sub" class="sub">{{ sub }}</div>
    <slot name="footer"></slot>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem 1.1rem;
  box-shadow: var(--shadow-sm);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
  margin-bottom: 0.4rem;
}

.label {
  font-size: 0.82rem;
  font-weight: 500;
}

.value-row {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.value {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-heading);
}

.unit {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.sub {
  margin-top: 0.3rem;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}
</style>
