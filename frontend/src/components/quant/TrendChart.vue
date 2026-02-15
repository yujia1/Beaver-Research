<template>
  <div class="trend-chart">
    <div class="chart-header">
      <h4>{{ metricName }}</h4>
      <span v-if="hasTrendData && trend" class="trend-badge" :class="trend.direction">
        {{ trend.direction }}
      </span>
    </div>
    <div v-if="!hasTrendData" class="no-data-message">
      No historical trend data available
    </div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'TrendChart',
  props: {
    trend: {
      type: Object,
      required: false,
      default: null
    },
    metricName: {
      type: String,
      required: true
    },
    isPercentage: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      chart: null
    }
  },
  computed: {
    hasTrendData() {
      return this.trend && 
             Array.isArray(this.trend.years) && 
             Array.isArray(this.trend.values) &&
             this.trend.years.length > 0 &&
             this.trend.values.length > 0
    },
    chartData() {
      if (!this.hasTrendData) {
        return {
          labels: [],
          datasets: []
        }
      }
      return {
        labels: this.trend.years,
        datasets: [{
          label: this.metricName,
          data: this.trend.values,
          borderColor: this.trendColor,
          backgroundColor: this.trendBackgroundColor,
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: this.trendColor,
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      }
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: {
              size: 14,
              weight: 'bold'
            },
            bodyFont: {
              size: 13
            },
            callbacks: {
              label: (context) => {
                const value = context.parsed.y
                if (this.isPercentage) {
                  return `${this.metricName}: ${(value * 100).toFixed(2)}%`
                }
                return `${this.metricName}: ${value.toFixed(2)}`
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
              font: {
                size: 12
              }
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              font: {
                size: 12
              },
              callback: (value) => {
                if (this.isPercentage) {
                  return `${(value * 100).toFixed(0)}%`
                }
                return value.toFixed(1)
              }
            }
          }
        }
      }
    },
    trendColor() {
      const direction = this.trend?.direction?.toLowerCase()
      if (direction === 'improving') return '#10b981'
      if (direction === 'declining') return '#ef4444'
      return '#6b7280'
    },
    trendBackgroundColor() {
      const direction = this.trend?.direction?.toLowerCase()
      if (direction === 'improving') return 'rgba(16, 185, 129, 0.1)'
      if (direction === 'declining') return 'rgba(239, 68, 68, 0.1)'
      return 'rgba(107, 114, 128, 0.1)'
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.renderChart()
    })
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy()
      this.chart = null
    }
  },
  watch: {
    trend: {
      deep: true,
      handler() {
        this.$nextTick(() => {
          this.updateChart()
        })
      }
    }
  },
  methods: {
    renderChart() {
      // Guard against missing data or refs
      if (!this.hasTrendData) return
      if (!this.$refs.chartCanvas) return
      
      // Ensure canvas is actually in the DOM and has dimensions
      const canvas = this.$refs.chartCanvas
      if (!canvas || !canvas.parentElement || canvas.offsetWidth === 0 || canvas.offsetHeight === 0) {
        console.warn('Canvas not ready for', this.metricName)
        // Retry after a short delay
        setTimeout(() => this.renderChart(), 100)
        return
      }
      
      try {
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          console.warn('Chart context not available for', this.metricName)
          return
        }
        
        // Destroy existing chart if present
        if (this.chart) {
          this.chart.destroy()
          this.chart = null
        }
        
        // Create new chart
        this.chart = new Chart(ctx, {
          type: 'line',
          data: this.chartData,
          options: this.chartOptions
        })
      } catch (error) {
        console.error('Error rendering chart for', this.metricName, error)
      }
    },
    updateChart() {
      if (!this.hasTrendData) {
        // If data is now invalid, destroy chart
        if (this.chart) {
          this.chart.destroy()
          this.chart = null
        }
        return
      }
      
      if (!this.chart) {
        this.renderChart()
        return
      }
      
      try {
        this.chart.data = this.chartData
        this.chart.options = this.chartOptions
        this.chart.update()
      } catch (error) {
        console.error('Error updating chart for', this.metricName, error)
        // Try to re-render on error
        this.renderChart()
      }
    }
  }
}
</script>

<style scoped>
.trend-chart {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.trend-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-badge.improving {
  background-color: #d1fae5;
  color: #065f46;
}

.trend-badge.declining {
  background-color: #fee2e2;
  color: #991b1b;
}

.trend-badge.stable {
  background-color: #e5e7eb;
  color: #374151;
}

.no-data-message {
  text-align: center;
  padding: 3rem 1rem;
  color: #9ca3af;
  font-size: 0.875rem;
  font-style: italic;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
}

canvas {
  max-height: 300px;
}
</style>
