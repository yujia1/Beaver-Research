<template>
  <div class="financial-chart-container">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps({
  type: {
    type: String,
    default: 'bar'
  },
  data: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const canvasRef = ref(null)
let chartInstance = null

const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  
  if (!canvasRef.value) return
  
  const ctx = canvasRef.value.getContext('2d')
  
  // Merge default options with props options
  const mergedOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    },
    ...props.options
  }

  chartInstance = new ChartJS(ctx, {
    type: props.type,
    data: props.data,
    options: mergedOptions
  })
}

onMounted(() => {
  renderChart()
})

watch(() => props.data, () => {
  nextTick(renderChart)
}, { deep: true })

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.financial-chart-container {
  width: 100%;
  height: 100%;
  min-height: 300px; /* Ensure default height */
}
</style>
