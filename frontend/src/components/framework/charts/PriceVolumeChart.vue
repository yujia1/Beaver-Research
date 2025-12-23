<template>
  <div class="price-volume-chart">
    <div class="chart-controls">
      <button 
        v-for="tf in timeframes" 
        :key="tf" 
        :class="['tf-btn', { active: selectedTimeframe === tf }]"
        @click="selectedTimeframe = tf"
      >
        {{ tf }}
      </button>
    </div>
    <div class="canvas-wrapper">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  symbol: {
    type: String,
    default: ''
  }
})

const canvasRef = ref(null)
let chartInstance = null
const selectedTimeframe = ref('ALL')
const timeframes = ['1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y', 'ALL']

const filteredData = computed(() => {
  if (!props.data || props.data.length === 0) return []
  
  // Daily data logic
  // Data is usually sorted by date desc or asc. FMP usually returns desc (newest first).
  // We need to sort asc for chart.
  const sorted = [...props.data].sort((a, b) => new Date(a.date) - new Date(b.date))
  
  const lastDate = new Date(sorted[sorted.length - 1].date)
  let cutoffDate = new Date(sorted[0].date) // default all
  
  switch (selectedTimeframe.value) {
    case '1M':
      cutoffDate = new Date(lastDate); cutoffDate.setMonth(lastDate.getMonth() - 1); break;
    case '3M':
      cutoffDate = new Date(lastDate); cutoffDate.setMonth(lastDate.getMonth() - 3); break;
    case '6M':
      cutoffDate = new Date(lastDate); cutoffDate.setMonth(lastDate.getMonth() - 6); break;
    case 'YTD':
      cutoffDate = new Date(lastDate.getFullYear(), 0, 1); break;
    case '1Y':
      cutoffDate = new Date(lastDate); cutoffDate.setFullYear(lastDate.getFullYear() - 1); break;
    case '3Y':
      cutoffDate = new Date(lastDate); cutoffDate.setFullYear(lastDate.getFullYear() - 3); break;
    case '5Y':
      cutoffDate = new Date(lastDate); cutoffDate.setFullYear(lastDate.getFullYear() - 5); break;
    default:
      return sorted // ALL
  }
  
  return sorted.filter(item => new Date(item.date) >= cutoffDate)
})

const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  
  if (!canvasRef.value || filteredData.value.length === 0) return
  
  const ctx = canvasRef.value.getContext('2d')
  
  const labels = filteredData.value.map(d => d.date)
  const prices = filteredData.value.map(d => d.close)
  const volumes = filteredData.value.map(d => d.volume)
  
  // Create gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 400)
  gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)') // Blue-500 equivalent
  gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)')
  
  // Calculate volume scale max to push bars down (make them take bottom 20%? or so)
  const maxVol = Math.max(...volumes)
  // If we want bars to be small, set Y-axis max for volume much higher than maxVol
  const volAxisMax = maxVol * 4 

  chartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: props.symbol ? `${props.symbol} Price` : 'Price',
          data: prices,
          borderColor: '#3b82f6', // Bright Blue
          backgroundColor: gradient,
          fill: true,
          tension: 0.1,
          pointRadius: 0, // Hide points for clean line
          pointHoverRadius: 4,
          borderWidth: 2,
          yAxisID: 'y'
        },
        {
          label: 'Volume',
          data: volumes,
          type: 'bar',
          backgroundColor: 'rgba(156, 163, 175, 0.5)', // Gray-400
          yAxisID: 'y1',
          barPercentage: 0.9,
          categoryPercentage: 0.9
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: {
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          callbacks: {
             label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                    label += ': ';
                }
                if (context.parsed.y !== null) {
                    if (context.dataset.type === 'bar') {
                        // Volume: format with compact notation
                        label += new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(context.parsed.y);
                    } else {
                        // Price
                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                    }
                }
                return label;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            maxTicksLimit: 8,
            maxRotation: 0
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: {
            color: '#f3f4f6'
          }
        },
        y1: {
          type: 'linear',
          display: false,
          position: 'left',
          min: 0,
          max: volAxisMax,
          grid: {
            display: false
          }
        }
      }
    }
  })
}

onMounted(() => {
  renderChart()
})

watch([filteredData, () => props.symbol], () => {
  nextTick(renderChart)
}, { deep: true })

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.price-volume-chart {
  width: 100%;
  height: 400px; /* Fixed height for image-like appearance */
  display: flex;
  flex-direction: column;
  background: white;
  padding: 1rem;
  box-sizing: border-box;
}

.chart-controls {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 1rem;
  background: #f3f4f6;
  width: fit-content;
  border-radius: 6px;
  padding: 2px;
}

.tf-group {
  display: flex;
}

.separator {
  margin: 0 8px;
  color: #9ca3af;
  font-size: 0.9em;
  user-select: none;
}


.tf-btn {
  background: transparent;
  border: none;
  padding: 4px 12px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.tf-btn:hover {
  color: #111827;
}

.tf-btn.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.canvas-wrapper {
  flex: 1;
  position: relative;
  min-height: 0; 
}
</style>
