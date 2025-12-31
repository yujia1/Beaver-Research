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
  },
  comparisonData: {
    type: Array, // [{ symbol: 'AAPL', data: [...] }]
    default: () => []
  }
})

const canvasRef = ref(null)
let chartInstance = null
const selectedTimeframe = ref('ALL')
const timeframes = ['1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y', 'ALL']
const colors = ['#ef4444', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899'] // Red, Green, Purple, Amber, Pink

const getCutoffDate = (data) => {
    if (!data || data.length === 0) return new Date(0);
    const sorted = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    const lastDate = new Date(sorted[sorted.length - 1].date);
    let cutoff = new Date(sorted[0].date);
    
    switch (selectedTimeframe.value) {
        case '1M':
            cutoff = new Date(lastDate); cutoff.setMonth(lastDate.getMonth() - 1); break;
        case '3M':
            cutoff = new Date(lastDate); cutoff.setMonth(lastDate.getMonth() - 3); break;
        case '6M':
            cutoff = new Date(lastDate); cutoff.setMonth(lastDate.getMonth() - 6); break;
        case 'YTD':
            cutoff = new Date(lastDate.getFullYear(), 0, 1); break;
        case '1Y':
            cutoff = new Date(lastDate); cutoff.setFullYear(lastDate.getFullYear() - 1); break;
        case '3Y':
            cutoff = new Date(lastDate); cutoff.setFullYear(lastDate.getFullYear() - 3); break;
        case '5Y':
            cutoff = new Date(lastDate); cutoff.setFullYear(lastDate.getFullYear() - 5); break;
        default:
            break;
    }
    return cutoff;
}

const filteredData = computed(() => {
  if (!props.data || props.data.length === 0) return []
  const sorted = [...props.data].sort((a, b) => new Date(a.date) - new Date(b.date))
  const cutoffDate = getCutoffDate(sorted)
  return sorted.filter(item => new Date(item.date) >= cutoffDate)
})

const filteredComparisonData = computed(() => {
    if (!props.comparisonData || props.comparisonData.length === 0) return [];
    
    // For cutoff, we use the main ticker's timeline or the comparison's own timeline?
    // Usually best to use main ticker's cutoff to keep X-axis consistent if we use its labels.
    // If we use common labels, we need to sync. 
    // For simplicity, we filter each dataset roughly by the same cutoff time logic calculated from ITS own data 
    // OR use the main data's cutoff specific date.
    // Let's use the main data's calculated cutoff date.
    
    let cutoffDate = new Date(0);
    if (props.data && props.data.length > 0) {
        cutoffDate = getCutoffDate(props.data);
    }
    
    return props.comparisonData.map(comp => {
         const sorted = [...comp.data].sort((a, b) => new Date(a.date) - new Date(b.date));
         return {
             ...comp,
             data: sorted.filter(item => new Date(item.date) >= cutoffDate)
         }
    });
})


const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  
  if (!canvasRef.value || filteredData.value.length === 0) return
  
  const ctx = canvasRef.value.getContext('2d')
  
  const mainData = filteredData.value
  const labels = mainData.map(d => d.date)
  const prices = mainData.map(d => d.close)
  const volumes = mainData.map(d => d.volume)
  
  // Create gradient for main
  const gradient = ctx.createLinearGradient(0, 0, 0, 400)
  gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)') // Blue-500 equivalent
  gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)')
  
  // Datasets
  const datasets = [
    {
      label: props.symbol ? `${props.symbol} Price` : 'Price',
      data: prices,
      borderColor: '#3b82f6', // Bright Blue
      backgroundColor: gradient,
      fill: true,
      tension: 0.1,
      pointRadius: 0, 
      pointHoverRadius: 4,
      borderWidth: 2,
      yAxisID: 'y',
      order: 1
    },
    {
      label: 'Volume',
      data: volumes,
      type: 'bar',
      backgroundColor: 'rgba(156, 163, 175, 0.5)', 
      yAxisID: 'y1',
      barPercentage: 0.9,
      categoryPercentage: 0.9,
      order: 3 // Put behind
    }
  ];
  
  // Add comparisons
  if (filteredComparisonData.value && filteredComparisonData.value.length > 0) {
      filteredComparisonData.value.forEach((comp, index) => {
          // Alignment check: We are using 'labels' from mainData. 
          // If comparison data is missing dates or has diff dates, it will be misaligned if we simply map data values.
          // Chart.js using 'category' scale requires data array length to match labels or be mapped object {x, y}.
          // Let's use mapped objects {x: date, y: price} for safety!
          // And update main dataset to use same format too, just in case.
          
          // Actually, if we switch to objects, we can just push data.
          // But 'labels' array defines the X axis bins in 'category' mode.
          // The cleanest correct way without TimeScale adapter is to map data to the specific label strings.
          
          const dataMap = new Map();
          comp.data.forEach(d => dataMap.set(d.date.split('T')[0], d.close));
          
          const alignedData = labels.map(dateStr => {
               // dateStr is 'YYYY-MM-DD' usually from FMP
               return dataMap.get(dateStr) || null; // null keeps line gap or spans
          });
          
          datasets.push({
              label: comp.symbol,
              data: alignedData,
              borderColor: colors[index % colors.length],
              backgroundColor: 'transparent',
              fill: false,
              tension: 0.1,
              pointRadius: 0,
              pointHoverRadius: 4,
              borderWidth: 2,
              yAxisID: 'y',
              order: 2
          });
      });
  }

  // Calculate volume scale max
  const maxVol = Math.max(...volumes)
  const volAxisMax = maxVol * 4 

  chartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: datasets
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

watch([filteredData, filteredComparisonData, () => props.symbol], () => {
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
