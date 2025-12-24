<template>
  <div class="chart-card">
    <div class="chart-header">
      <h2>{{ title }}</h2>
      <div class="timeframe-selector">
        <button 
          v-for="period in timePeriods" 
          :key="period.value" 
          :class="{ active: selectedTimePeriod === period.value }"
          @click="selectPeriod(period.value)"
        >
          {{ period.label }}
        </button>
      </div>
    </div>
    <div class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps({
  stockData: {
    type: Array,
    required: true
  },
  selectedTimePeriod: {
    type: String, // 'daily', 'weekly', etc.
    default: 'daily'
  },
  title: {
    type: String,
    default: 'Price Timeline'
  }
})

const emit = defineEmits(['update:selectedTimePeriod'])

const { t } = useI18n()

const timePeriods = computed(() => [
  { label: t('investment.timeframes.daily'), value: 'daily' },
  { label: t('investment.timeframes.weekly'), value: 'weekly' },
  { label: t('investment.timeframes.monthly'), value: 'monthly' },
  { label: t('investment.timeframes.yearly'), value: 'yearly' },
  { label: t('investment.timeframes.max'), value: 'max' }
])

function selectPeriod(period) {
  emit('update:selectedTimePeriod', period)
}

// Filter logic (Moved from Parent)
const filteredStockData = computed(() => {
  const allData = props.stockData
  
  if (!allData || allData.length === 0) {
    return []
  }
  
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  let startDate = new Date()
  
  switch (props.selectedTimePeriod) {
    case 'daily':
      startDate.setDate(today.getDate() - 30)
      break
    case 'weekly':
      startDate.setDate(today.getDate() - 84)
      break
    case 'monthly':
      startDate.setMonth(today.getMonth() - 12)
      break
    case 'yearly':
      startDate.setFullYear(today.getFullYear() - 5)
      break
    case 'max':
    default:
      return allData
  }
  
  startDate.setHours(0, 0, 0, 0)
  return allData.filter(d => {
    const dataDate = new Date(d.date)
    dataDate.setHours(0, 0, 0, 0)
    return dataDate >= startDate
  })
})

const chartData = computed(() => {
  const dataToUse = filteredStockData.value
  
  if (!dataToUse || dataToUse.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: 'Stock Price',
        data: [],
        borderColor: '#3498db',
        backgroundColor: 'rgba(52, 152, 219, 0.1)',
        fill: false,
        tension: 0.4
      }]
    }
  }
  
  const labels = dataToUse.map((d, index) => {
    const date = new Date(d.date)
    
    if (props.selectedTimePeriod === 'daily') {
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      return `${month} ${day}`
    } else if (props.selectedTimePeriod === 'weekly') {
      if (index % 7 === 0 || index === 0) {
        const month = date.toLocaleString('default', { month: 'short' })
        const day = date.getDate()
        return `${month} ${day}`
      }
      return ''
    } else if (props.selectedTimePeriod === 'monthly') {
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      const year = date.getFullYear()
      return `${month} ${day}, ${year}`
    } else if (props.selectedTimePeriod === 'yearly') {
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      const year = date.getFullYear()
      return `${month} ${day}, ${year}`
    } else {
      if (date.getDate() === 1 || index === 0 || index === dataToUse.length - 1) {
        const month = date.toLocaleString('default', { month: 'short' })
        const year = date.getFullYear()
        return `${month} ${year}`
      }
      return ''
    }
  })
  
  const prices = dataToUse.map(d => d.price)
  
  const datasets = [
    {
      label: 'Stock Price',
      data: prices,
      borderColor: '#3498db',
      backgroundColor: 'rgba(52, 152, 219, 0.1)',
      fill: false,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 4
    }
  ]
  
  return {
    labels,
    datasets
  }
})

const chartOptions = computed(() => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    backgroundColor: '#ffffff',
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        titleColor: '#000000',
        bodyColor: '#000000',
        borderColor: '#cccccc',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          title: function(context) {
            return context[0].label
          },
          label: function(context) {
            if (context.datasetIndex === 0) {
              return `Price: $${context.parsed.y.toFixed(2)}`
            }
            return null
          },
          labelColor: function(context) {
            return {
              borderColor: '#3498db',
              backgroundColor: '#3498db'
            }
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          color: '#666666',
          maxTicksLimit: props.selectedTimePeriod === 'daily' ? 30 : 
                         props.selectedTimePeriod === 'weekly' ? 12 :
                         props.selectedTimePeriod === 'monthly' ? 12 :
                         props.selectedTimePeriod === 'yearly' ? 5 : 20,
          callback: function(value) {
            const label = this.getLabelForValue(value)
            return label || ''
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          color: '#666666',
          callback: function(value) {
            return '$' + value.toFixed(0)
          }
        }
      }
    }
  }
})
</script>

<style scoped>
.chart-card {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid #eaeaea;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.chart-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: #000000;
}

.timeframe-selector {
  display: flex;
  gap: 0.5rem;
}

.timeframe-selector button {
  padding: 0.5rem 1rem;
  border: 1px solid #e0e0e0;
  background-color: #ffffff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #666666;
  font-weight: 500;
  transition: all 0.2s;
}

.timeframe-selector button.active {
  background-color: #000000;
  color: #ffffff;
  border-color: #000000;
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style>
