<script setup>
import { computed } from 'vue'
import VueFeather from 'vue-feather'

const props = defineProps({
  risk: { type: String, default: 'none' }, // 'none' | 'low' | 'high'
  correctedTemperature: { type: Number, default: null },
})

const config = computed(() => {
  if (props.risk === 'high') {
    return {
      icon: 'sun',
      label: 'Fort ensoleillement possible',
      detail: props.correctedTemperature !== null
        ? `Le capteur est en plein soleil : la température peut être surestimée. Si le ciel est dégagé, la valeur réelle est plutôt proche de ${props.correctedTemperature} °C.`
        : 'Le capteur est en plein soleil : la température peut être surestimée si le ciel est dégagé.',
      class: 'risk-high',
    }
  }
  if (props.risk === 'low') {
    return {
      icon: 'sunrise',
      label: 'Soleil bas',
      detail: 'Soleil proche de l\'horizon : léger risque de surestimation si le ciel est dégagé.',
      class: 'risk-low',
    }
  }
  return {
    icon: 'moon',
    label: 'Pas de biais solaire',
    detail: 'Nuit ou soleil trop bas : la mesure de température est fiable.',
    class: 'risk-none',
  }
})
</script>

<template>
  <span class="sun-badge" :class="config.class" :title="config.detail">
    <vue-feather :type="config.icon" size="14"></vue-feather>
    <span>{{ config.label }}</span>
  </span>
</template>

<style scoped>
.sun-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: help;
}

.risk-none {
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}

.risk-low {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.risk-high {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}
</style>
