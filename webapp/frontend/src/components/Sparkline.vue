<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale, Filler } from 'chart.js'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Filler)

const props = defineProps({
  labels: { type: Array, required: true },
  data: { type: Array, required: true },
  color: { type: String, default: '#2f7fd6' },
})

const chartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      data: props.data,
      borderColor: props.color,
      backgroundColor: props.color + '22',
      borderWidth: 2,
      pointRadius: 0,
      fill: true,
      tension: 0.35,
      spanGaps: true,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  scales: {
    x: { display: false },
    y: { display: false },
  },
  elements: { line: { capBezierPoints: true } },
}
</script>

<template>
  <div class="sparkline">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.sparkline {
  height: 40px;
  width: 100%;
}
</style>
