<template>
  <div class="balance-sheet-yearly-table">
    <div v-if="yearlyData.length === 0" class="no-data">
      No yearly data available
    </div>
    
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>Year</th>
            <th>Net Debt</th>
            <th>EBITDA</th>
            <th>Capitalized Costs</th>
            <th>Revenue</th>
            <th>Net Debt/EBITDA</th>
            <th>Cap Costs/Revenue</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="row in yearlyData" 
            :key="row.year"
            :class="{ 'red-flag-row': row.is_red_flag }"
          >
            <td class="year-cell">{{ row.year }}</td>
            <td class="value-cell">{{ formatCurrency(row.net_debt) }}</td>
            <td class="value-cell">{{ formatCurrency(row.ebitda) }}</td>
            <td class="value-cell">{{ formatCurrency(row.capitalized_costs) }}</td>
            <td class="value-cell">{{ formatCurrency(row.revenue) }}</td>
            <td class="ratio-cell">{{ formatRatio(row.net_debt_to_ebitda) }}</td>
            <td class="ratio-cell">{{ formatPercentage(row.capitalized_costs_to_revenue) }}</td>
            <td class="status-cell">
              <span v-if="row.is_red_flag" class="red-flag-badge" :title="row.red_flag_reason">
                Red Flag
              </span>
              <span v-else class="ok-badge">OK</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BalanceSheetYearlyTable',
  props: {
    yearlyData: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  methods: {
    formatCurrency(value) {
      if (value === null || value === undefined) return 'N/A'
      
      const absValue = Math.abs(value)
      if (absValue >= 1e9) {
        return `$${(value / 1e9).toFixed(2)}B`
      } else if (absValue >= 1e6) {
        return `$${(value / 1e6).toFixed(2)}M`
      } else if (absValue >= 1e3) {
        return `$${(value / 1e3).toFixed(2)}K`
      }
      return `$${value.toFixed(2)}`
    },
    
    formatRatio(value) {
      if (value === null || value === undefined) return 'N/A'
      return `${value.toFixed(2)}x`
    },
    
    formatPercentage(value) {
      if (value === null || value === undefined) return 'N/A'
      return `${(value * 100).toFixed(2)}%`
    }
  }
}
</script>

<style scoped>
.balance-sheet-yearly-table {
  width: 100%;
  margin-bottom: 2rem;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  white-space: nowrap;
}

tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background 0.2s;
}

tbody tr:hover {
  background: #f9fafb;
}

tbody tr.red-flag-row {
  /* No special style */
}

tbody tr.red-flag-row:hover {
  background: #f9fafb;
}

td {
  padding: 1rem;
  font-size: 0.875rem;
}

.year-cell {
  font-weight: 600;
  color: #111827;
  font-size: 1rem;
}

.value-cell {
  font-family: 'Monaco', 'Courier New', monospace;
  font-weight: 600;
  color: #374151;
}

.ratio-cell {
  font-family: 'Monaco', 'Courier New', monospace;
  font-weight: 700;
  color: #000;
}

.status-cell {
  text-align: center;
}

.red-flag-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: help;
}

.ok-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: #d1fae5;
  color: #059669;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
  font-style: italic;
}
</style>
