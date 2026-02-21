<template>
  <div class="quant-screener-view">

    <!-- Input Section -->
    <div class="input-section">
      <div class="input-group">
        <input
          v-model="ticker"
          type="text"
          placeholder="Enter ticker, e.g., AAPL"
          @keyup.enter="screenStock"
          :disabled="loading"
          class="ticker-input"
        />
        <button
          @click="screenStock"
          :disabled="loading || !ticker.trim()"
          class="screen-button"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? 'Screening...' : 'Screen' }}
        </button>
      </div>
      <div v-if="saveMessage" class="save-message" :class="{ success: saveSuccess, error: !saveSuccess }">
        {{ saveMessage }}
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-alert">
      <span>Error</span>
      <span>{{ error }}</span>
      <button @click="error = null" class="close-button">×</button>
    </div>

    <!-- Results -->
    <div v-if="layeredResult" class="results-section">

      <!-- Header + Action -->
      <div class="results-header">
        <div>
          <h2>{{ layeredResult.ticker }}</h2>
          <span class="sub-label">Layered Screener — {{ layeredResult.survival_filter.yearly.length }} years of data</span>
        </div>
        <div class="action-badge" :class="actionClass">
          {{ layeredResult.action.recommendation }}
        </div>
      </div>

      <!-- Action detail -->
      <div class="action-detail">
        <strong>{{ layeredResult.action.reason }}</strong>
        <span class="divider">·</span>
        <em>{{ layeredResult.action.size_note }}</em>
        <button @click="saveLayeredResult" :disabled="saving" class="save-button" style="margin-left:auto">
          <span v-if="saving" class="loading-spinner"></span>
          {{ saving ? 'Saving...' : 'Save to Flagged Companies' }}
        </button>
      </div>

      <!-- Layer Tabs -->
      <div class="layer-tabs">
        <button
          v-for="tab in layerTabs"
          :key="tab.key"
          class="layer-tab"
          :class="{ active: activeLayer === tab.key, 'has-flag': tab.hasFlag }"
          @click="activeLayer = tab.key"
        >
          <span class="tab-flag-dot" v-if="tab.hasFlag">●</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- ── Layer 1: Survival Filter ── -->
      <div v-if="activeLayer === 'survival'" class="layer-panel">
        <div class="layer-status" :class="layeredResult.survival_filter.top_reasons && layeredResult.survival_filter.top_reasons.length ? 'fail' : 'pass'">
          <span>{{ (layeredResult.survival_filter.top_reasons && layeredResult.survival_filter.top_reasons.length) ? '✗ FAIL' : '✓ PASS' }}</span>
          <span v-if="layeredResult.survival_filter.top_reasons && layeredResult.survival_filter.top_reasons.length" class="flag-reasons">
            {{ layeredResult.survival_filter.top_reasons.join(' · ') }}
          </span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>Current Ratio <span class="threshold">≥ 1.0</span></th>
                <th>Interest Burden <span class="threshold">≥ 2.0</span></th>
                <th>Net Debt/EBITDA <span class="threshold">≤ 4.0</span></th>
                <th>FCF</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in layeredResult.survival_filter.yearly" :key="row.year" :class="{ 'row-fail': row.is_red_flag }">
                <td class="year-cell">{{ row.year }}</td>
                <td :class="cellClass(row.current_ratio_pass)">{{ fmtRatio(row.current_ratio) }}</td>
                <td :class="cellClass(row.interest_burden_pass)">{{ fmtRatio(row.interest_burden) }}</td>
                <td :class="cellClass(row.net_debt_pass)">{{ fmtRatio(row.net_debt_to_ebitda) }}</td>
                <td class="mono">{{ fmtCurrency(row.fcf) }}</td>
                <td>
                  <span class="badge" :class="row.is_red_flag ? 'badge-fail' : 'badge-pass'">
                    {{ row.is_red_flag ? 'Flag' : 'OK' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Layer 2: Earnings Quality ── -->
      <div v-if="activeLayer === 'earnings'" class="layer-panel">
        <div v-if="layeredResult.earnings_quality.notes && layeredResult.earnings_quality.notes.length" class="layer-notes">
          <span v-for="(n, i) in layeredResult.earnings_quality.notes" :key="i" class="note-chip flag">{{ n }}</span>
        </div>
        <div v-else class="layer-notes clean">No earnings quality red flags.</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>CFO / Net Income <span class="threshold">0.8–1.2</span></th>
                <th>FCF / Net Income <span class="threshold">&gt; 0</span></th>
                <th>Capex / Rev</th>
                <th>SBC / Rev</th>
                <th>Shares Out</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in layeredResult.earnings_quality.yearly" :key="row.year" :class="{ 'row-fail': row.is_red_flag }">
                <td class="year-cell">{{ row.year }}</td>
                <td :class="cellClass(row.cfo_to_ni_pass)">{{ fmtRatio(row.cfo_to_ni) }}</td>
                <td :class="cellClass(row.fcf_to_ni_pass)">{{ fmtRatio(row.fcf_to_ni) }}</td>
                <td class="mono">{{ fmtPct(row.capex_to_rev) }}</td>
                <td class="mono">{{ fmtPct(row.sbc_to_rev) }}</td>
                <td class="mono">{{ fmtLargeNum(row.shares_out) }}</td>
                <td>
                  <span class="badge" :class="row.is_red_flag ? 'badge-fail' : 'badge-pass'">
                    {{ row.is_red_flag ? 'Flag' : 'OK' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Layer 3: Structural Health ── -->
      <div v-if="activeLayer === 'structural'" class="layer-panel">
        <div v-if="layeredResult.structural_health.notes && layeredResult.structural_health.notes.length" class="layer-notes">
          <span v-for="(n, i) in layeredResult.structural_health.notes" :key="i" class="note-chip flag">{{ n }}</span>
        </div>
        <div v-else class="layer-notes clean">No structural health concerns.</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>ROIC</th>
                <th>Gross Margin</th>
                <th>Op Margin</th>
                <th>Cost of Debt</th>
                <th>ROIC Spread <span class="threshold">&gt; 0</span></th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in layeredResult.structural_health.yearly" :key="row.year" :class="{ 'row-fail': row.is_red_flag }">
                <td class="year-cell">{{ row.year }}</td>
                <td class="mono">{{ fmtPct(row.roic) }}</td>
                <td class="mono">{{ fmtPct(row.gross_margin) }}</td>
                <td class="mono">{{ fmtPct(row.op_margin) }}</td>
                <td class="mono">{{ fmtPct(row.cost_of_debt) }}</td>
                <td :class="cellClass(row.roic_spread !== null ? row.roic_spread >= 0 : null)">{{ fmtPct(row.roic_spread) }}</td>
                <td>
                  <span class="badge" :class="row.is_red_flag ? 'badge-fail' : 'badge-pass'">
                    {{ row.is_red_flag ? 'Flag' : 'OK' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Layer 4: Valuation ── -->
      <div v-if="activeLayer === 'valuation'" class="layer-panel">
        <div v-if="layeredResult.valuation.notes && layeredResult.valuation.notes.length" class="layer-notes">
          <span v-for="(n, i) in layeredResult.valuation.notes" :key="i" class="note-chip flag">{{ n }}</span>
        </div>
        <div v-else class="layer-notes clean">Valuation looks reasonable.</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>FCF Yield <span class="threshold">≥ 5% Buy</span></th>
                <th>EV/EBITDA</th>
                <th>P/E</th>
                <th>EPS Growth</th>
                <th>PEG</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in layeredResult.valuation.yearly" :key="row.year" :class="{ 'row-fail': row.is_red_flag }">
                <td class="year-cell">{{ row.year }}</td>
                <td :class="cellClass(row.fcf_yield_pass)">{{ fmtPct(row.fcf_yield) }}</td>
                <td class="mono">{{ fmtRatio(row.ev_ebitda) }}</td>
                <td class="mono">{{ fmtRatio(row.pe) }}</td>
                <td class="mono">{{ fmtPct(row.eps_growth) }}</td>
                <td class="mono">{{ fmtRatio(row.peg) }}</td>
                <td>
                  <span class="badge" :class="row.is_red_flag ? 'badge-fail' : 'badge-pass'">
                    {{ row.is_red_flag ? 'Flag' : 'OK' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import API_BASE_URL from '@/config/api'

const api = axios.create({ baseURL: API_BASE_URL })

export default {
  name: 'QuantScreenerView',
  data() {
    return {
      ticker: '',
      screenedTicker: '',
      layeredResult: null,
      activeLayer: 'survival',
      loading: false,
      saving: false,
      error: null,
      saveMessage: null,
      saveSuccess: false,
    }
  },

  computed: {
    actionClass() {
      if (!this.layeredResult) return ''
      const rec = this.layeredResult.action.recommendation
      if (rec === 'Buy')   return 'action-buy'
      if (rec === 'Avoid') return 'action-avoid'
      return 'action-watch'
    },

    layerTabs() {
      if (!this.layeredResult) return []
      const r = this.layeredResult
      return [
        {
          key: 'survival',
          label: 'Survival Filter',
          hasFlag: r.survival_filter.top_reasons && r.survival_filter.top_reasons.length > 0,
        },
        {
          key: 'earnings',
          label: 'Earnings Quality',
          hasFlag: r.earnings_quality.notes && r.earnings_quality.notes.length > 0,
        },
        {
          key: 'structural',
          label: 'Structural Health',
          hasFlag: r.structural_health.notes && r.structural_health.notes.length > 0,
        },
        {
          key: 'valuation',
          label: 'Valuation',
          hasFlag: r.valuation.notes && r.valuation.notes.length > 0,
        },
      ]
    },
  },

  methods: {
    async screenStock() {
      if (!this.ticker.trim()) return

      this.loading = true
      this.error = null
      this.layeredResult = null
      this.activeLayer = 'survival'

      try {
        const t = this.ticker.trim().split(',')[0].trim()
        const response = await api.get(`/api/quant/screener/fmp-layered/${t}?limit=5&period=FY`)

        if (response.data) {
          this.layeredResult = response.data
          this.screenedTicker = response.data.ticker
          this.saveMessage = null
        } else {
          this.error = 'No data returned for the specified ticker'
        }
      } catch (err) {
        console.error('Screening error:', err)
        this.error = err.response?.data?.detail || err.message || 'Failed to screen stock'
      } finally {
        this.loading = false
      }
    },

    async saveLayeredResult() {
      if (!this.screenedTicker || !this.layeredResult) return

      this.saving = true
      this.saveMessage = null

      try {
        await api.post('/api/quant/screener/fmp-layered/flagged', Object.assign({}, this.layeredResult))
        this.saveMessage = `Successfully saved ${this.screenedTicker.toUpperCase()} to Flagged Companies!`
        this.saveSuccess = true
        setTimeout(() => { this.saveMessage = null }, 5000)
      } catch (err) {
        console.error('Save layered error:', err)
        this.saveMessage = err.response?.data?.detail || 'Failed to save layered result'
        this.saveSuccess = false
        setTimeout(() => { this.saveMessage = null }, 5000)
      } finally {
        this.saving = false
      }
    },

    // ── Formatters ──
    fmtRatio(v) {
      if (v === null || v === undefined) return '—'
      return `${parseFloat(v).toFixed(2)}×`
    },
    fmtPct(v) {
      if (v === null || v === undefined) return '—'
      return `${(parseFloat(v) * 100).toFixed(2)}%`
    },
    fmtCurrency(v) {
      if (v === null || v === undefined) return '—'
      const n = parseFloat(v)
      const abs = Math.abs(n)
      if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
      if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
      if (abs >= 1e3) return `$${(n / 1e3).toFixed(2)}K`
      return `$${n.toFixed(2)}`
    },
    fmtLargeNum(v) {
      if (v === null || v === undefined) return '—'
      const n = parseFloat(v)
      const abs = Math.abs(n)
      if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}B`
      if (abs >= 1e6) return `${(n / 1e6).toFixed(2)}M`
      if (abs >= 1e3) return `${(n / 1e3).toFixed(2)}K`
      return n.toFixed(0)
    },
    cellClass(pass) {
      if (pass === null || pass === undefined) return 'mono'
      return pass ? 'mono cell-pass' : 'mono cell-fail'
    },
  }
}
</script>

<style scoped>
.quant-screener-view {
  max-width: 1300px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Input */
.input-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  border: 1px solid #e4e4e7;
  margin-bottom: 1.5rem;
}

.input-group {
  display: flex;
  gap: 0.75rem;
}

.ticker-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color .2s;
}
.ticker-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,.12);
}

.screen-button,
.save-button {
  padding: 0.6rem 1.4rem;
  background: #18181b;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
  transition: background .2s, transform .1s;
}
.screen-button:hover:not(:disabled),
.save-button:hover:not(:disabled) { background: #3f3f46; transform: translateY(-1px); }
.screen-button:disabled,
.save-button:disabled { opacity: .55; cursor: not-allowed; }

/* Error */
.error-alert {
  background: #fef2f2;
  border-left: 4px solid #ef4444;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}
.close-button {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #ef4444;
  cursor: pointer;
}

/* Save Message */
.save-message {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}
.save-message.success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
.save-message.error   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

/* Results */
.results-section {
  background: white;
  border-radius: 12px;
  border: 1px solid #e4e4e7;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  overflow: hidden;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem 1rem;
  border-bottom: 1px solid #f1f1f3;
}
.results-header h2 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
  color: #18181b;
}
.sub-label {
  font-size: 0.8rem;
  color: #71717a;
  display: block;
  margin-top: 2px;
}

.action-badge {
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.9rem;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.action-buy   { background: #d1fae5; color: #065f46; }
.action-avoid { background: #fee2e2; color: #991b1b; }
.action-watch { background: #fef9c3; color: #854d0e; }

.action-detail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 2rem 1rem;
  font-size: 0.875rem;
  color: #52525b;
  border-bottom: 1px solid #f1f1f3;
  flex-wrap: wrap;
}
.divider { color: #d1d5db; }

/* Layer Tabs */
.layer-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #f1f1f3;
  background: #fafafa;
  padding: 0 1rem;
}

.layer-tab {
  padding: 0.75rem 1.25rem;
  border: none;
  background: none;
  font-size: 0.875rem;
  font-weight: 600;
  color: #71717a;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: color .15s, border-color .15s;
}
.layer-tab:hover { color: #18181b; }
.layer-tab.active { color: #18181b; border-bottom-color: #18181b; }
.layer-tab.has-flag .tab-flag-dot { color: #ef4444; font-size: 0.6rem; }
.layer-tab.active.has-flag { color: #dc2626; border-bottom-color: #dc2626; }

/* Layer Panel */
.layer-panel {
  padding: 1.5rem 2rem;
}

.layer-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}
.layer-status.pass { background: #d1fae5; color: #065f46; }
.layer-status.fail { background: #fee2e2; color: #991b1b; }
.flag-reasons { font-weight: 400; font-size: 0.8rem; }

.layer-notes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  font-size: 0.875rem;
}
.layer-notes.clean { color: #16a34a; font-weight: 500; }
.note-chip { padding: 0.3rem 0.8rem; border-radius: 999px; font-size: 0.8rem; font-weight: 500; }
.note-chip.flag { background: #fee2e2; color: #dc2626; }

/* Table */
.table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e4e4e7;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

thead {
  background: #f9fafb;
  border-bottom: 2px solid #e4e4e7;
}
th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 700;
  color: #374151;
  white-space: nowrap;
}
.threshold {
  font-weight: 400;
  color: #9ca3af;
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

tbody tr {
  border-bottom: 1px solid #f3f4f6;
  transition: background .15s;
}
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: #f9fafb; }
tbody tr.row-fail { background: #fff8f8; }
tbody tr.row-fail:hover { background: #fff1f1; }

td { padding: 0.7rem 1rem; }

.year-cell {
  font-weight: 700;
  color: #18181b;
  font-size: 0.95rem;
}

.mono {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  color: #374151;
}

.cell-pass { font-family: 'Monaco', monospace; color: #059669; font-weight: 700; }
.cell-fail { font-family: 'Monaco', monospace; color: #dc2626; font-weight: 700; }

.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.badge-pass { background: #d1fae5; color: #059669; }
.badge-fail { background: #fee2e2; color: #dc2626; }

/* Spinner */
.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Responsive */
@media (max-width: 768px) {
  .quant-screener-view { padding: 1rem; }
  .input-group { flex-direction: column; }
  .results-header { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
  .action-detail { flex-direction: column; align-items: flex-start; }
  .layer-tabs { overflow-x: auto; }
  .layer-tab { flex-shrink: 0; }
}
</style>
