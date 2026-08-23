<script setup>
defineProps({
  modelValue: { type: Boolean, required: true },
  label: { type: String, required: true },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <label class="toggle-row">
    <span>{{ label }}</span>
    <span
      class="switch"
      :class="{ on: modelValue }"
      role="switch"
      :aria-checked="modelValue"
      tabindex="0"
      @click="$emit('update:modelValue', !modelValue)"
      @keydown.space.prevent="$emit('update:modelValue', !modelValue)"
      @keydown.enter.prevent="$emit('update:modelValue', !modelValue)"
    >
      <span class="knob"></span>
    </span>
  </label>
</template>

<style scoped>
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.5rem 0;
  cursor: pointer;
  font-size: 0.92rem;
  color: var(--color-text);
}

.switch {
  position: relative;
  width: 40px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  transition: background-color 0.15s;
}

.switch.on {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
}

.switch.on .knob {
  transform: translateX(16px);
}
</style>
