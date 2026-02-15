<template>
  <div class="screener-metrics-table">
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Latest Value</th>
          <th>Components</th>
          <th v-if="showTrend">Trend</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="(metric, key) in metrics" 
          :key="key"
          :class="{ 'red-flag': metric.is_red_flag }"
          @click="$emit('metric-click', key)"
        >
          <td class="metric-name">{{ metric.name }}</td>
          <td class="metric-value">{{ formatValue(metric.latest_value, key) }}</td>
          <td class="metric-components">
            <div v-if="metric.component_values" class="components-grid">
              <div v-for="(value, compKey) in metric.component_values" :key="compKey" class="component-item">
                <span class="component-label">{{ formatComponentLabel(compKey) }}:</span>
                <span class="component-value">{{ formatComponentValue(value, compKey) }}</span>
              </div>
            </div>
            <span v-else class="no-components">—</span>
          </td>
          <td v-if="showTrend" class="metric-trend">
            <TrendIndicator v-if="metric.trend" :trend="metric.trend" />
            <span v-else class="no-trend">N/A</span>
          </td>
          <td class="metric-status">
            <RedFlagBadge 
              v-if="metric.is_red_flag" 
              :reason="metric.red_flag_reason || 'Red flag detected'" 
            />
            <span v-else class="ok-badge">OK</span>
          </td>
        </tr>
      </tbody>
    </table>
    
    <div v-if="Object.keys(metrics).length === 0" class="no-data">
      No metrics available
    </div>
  </div>
</template>

<script>
import RedFlagBadge from './RedFlagBadge.vue'
import TrendIndicator from './TrendIndicator.vue'

export default {
  name: 'ScreenerMetricsTable',
  components: {
    RedFlagBadge,
    TrendIndicator
  },
  props: {
    metrics: {
      type: Object,
      required: true,
      default: () => ({})
    },
    showTrend: {
      type: Boolean,
      default: true
    }
  },
  emits: ['metric-click'],
  methods: {
    formatValue(value, metricKey) {
      if (value === null || value === undefined) return 'N/A'
      
      // Percentage metrics
      if (['fcf_to_revenue', 'fcf_to_dividends_buybacks'].includes(metricKey)) {
        return `${(value * 100).toFixed(2)}%`
      }
      
      // Ratio metrics
      if (['net_debt_to_ebitda', 'ev_to_revenue', 'ev_to_ebitda', 'capitalized_costs_to_revenue'].includes(metricKey)) {
        return `${value.toFixed(2)}x`
      }
      
      // Days metrics
      if (metricKey === 'days_sales_outstanding') {
        return `${value.toFixed(0)} days`
      }
      
      // Channel stuffing risk (ratio)
      if (metricKey === 'channel_stuffing_risk') {
        return value.toFixed(3)
      }
      
      return value.toFixed(2)
    },
    
    formatComponentLabel(key) {
      const labels = {
        'fcf': 'FCF',
        'dividends_buybacks': 'Dividends + Buybacks',
        'revenue': 'Revenue',
        'net_debt': 'Net Debt',
        'ebitda': 'EBITDA',
        'capitalized_costs': 'Capitalized Costs',
        'accounts_receivable': 'Accounts Receivable',
        'enterprise_value': 'Enterprise Value',
        'ar_growth': 'AR Growth',
        'revenue_growth': 'Revenue Growth',
        'dso_current': 'DSO Current',
        'dso_previous': 'DSO Previous',
        'ar_current': 'AR Current',
        'ar_previous': 'AR Previous',
        'revenue_current': 'Revenue Current',
        'revenue_previous': 'Revenue Previous'
      }
      return labels[key] || key
    },
    
    formatComponentValue(value, key) {
      if (value === null || value === undefined) return 'N/A'
      
      // Growth rates
      if (key.includes('growth')) {
        return `${(value * 100).toFixed(1)}%`
      }
      
      // DSO values
      if (key.includes('dso')) {
        return `${value.toFixed(1)} days`
      }
      
      // Currency values (large numbers)
      if (['fcf', 'dividends_buybacks', 'revenue', 'net_debt', 'ebitda', 
           'capitalized_costs', 'accounts_receivable', 'enterprise_value',
           'ar_current', 'ar_previous', 'revenue_current', 'revenue_previous'].includes(key)) {
        if (Math.abs(value) >= 1e9) {
          return `$${(value / 1e9).toFixed(2)}B`
        } else if (Math.abs(value) >= 1e6) {
          return `$${(value / 1e6).toFixed(2)}M`
        } else if (Math.abs(value) >= 1e3) {
          return `$${(value / 1e3).toFixed(2)}K`
        }
        return `$${value.toFixed(2)}`
      }
      
      return value.toFixed(2)
    }
  }
}
</script>

<style scoped>
.screener-metrics-table {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.2s;
  cursor: pointer;
}

tbody tr:hover {
  background-color: #f9fafb;
}

tbody tr.red-flag {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
}

tbody tr.red-flag:hover {
  background-color: #fee2e2;
}

td {
  padding: 1rem;
  font-size: 0.875rem;
}

.metric-name {
  font-weight: 500;
  color: #374151;
}

.metric-value {
  font-weight: 600;
  color: #1f2937;
  font-family: 'Monaco', 'Courier New', monospace;
}

.metric-components {
  font-size: 0.8125rem;
  max-width: 300px;
}

.components-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.25rem;
}

.component-item {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.125rem 0;
}

.component-label {
  color: #6b7280;
  font-weight: 500;
  white-space: nowrap;
}

.component-value {
  color: #374151;
  font-weight: 600;
  font-family: 'Monaco', 'Courier New', monospace;
  text-align: right;
}

.no-components {
  color: #9ca3af;
  font-style: italic;
}

.metric-trend {
  min-width: 120px;
}

.metric-status {
  text-align: center;
}

.ok-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  background-color: #f0fdf4;
  color: #16a34a;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.no-trend {
  color: #9ca3af;
  font-style: italic;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  th, td {
    padding: 0.75rem 0.5rem;
    font-size: 0.8125rem;
  }
  
  .metric-trend {
    min-width: 100px;
  }
}
</style>
