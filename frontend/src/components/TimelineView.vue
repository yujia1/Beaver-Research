<template>
  <div class="timeline-view">
    <div class="page-header">
      <div>
        <h1>Stock Price Timeline</h1>
        <p class="subtitle">Track stock price movements and key events over time</p>
      </div>
      <div class="price-info">
        <div class="current-price">${{ currentPrice.toFixed(2) }}</div>
        <div class="price-change" :class="priceChange >= 0 ? 'positive' : 'negative'">
          {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }} ({{ priceChangePercent >= 0 ? '+' : '' }}{{ priceChangePercent.toFixed(2) }}%) since {{ referenceDate }}
        </div>
      </div>
    </div>

    <!-- Stock Selection -->
    <div class="stock-selector">
      <label for="stock-search">Search Stock:</label>
      <input 
        id="stock-search" 
        v-model="stockSearchInput" 
        type="text" 
        placeholder="Enter ticker symbol (e.g., TSLA, AAPL, MSFT)"
        @keyup.enter="searchStock"
      />
      <button @click="searchStock" :disabled="loadingStock">Search</button>
      <div v-if="loadingStock" class="loading-indicator">Loading...</div>
      <div v-if="stockError" class="stock-error">{{ stockError }}</div>
    </div>

    <!-- Chart Section -->
    <div class="chart-card">
      <div class="chart-header">
        <h2>{{ selectedStock }} - {{ timelineYear }} Price Timeline</h2>
        <div class="timeframe-selector">
          <button 
            v-for="period in timePeriods" 
            :key="period.value" 
            :class="{ active: selectedTimePeriod === period.value }"
            @click="selectedTimePeriod = period.value"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
      <div class="chart-container">
        <Line :key="`chart-${events.length}-${eventFilters.positive}-${eventFilters.negative}-${eventFilters.neutral}-${categoryFilters.macro}-${categoryFilters.micro}-${categoryFilters.market}-${categoryFilters.industry}-${categoryFilters.product}-${forecastFilters.actual}-${selectedTimePeriod}`" :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Key Events Section -->
    <div class="events-card">
      <div class="events-header">
        <h2>Key Logs</h2>
        <button v-if="activeTab === 'events'" class="add-event-btn" @click="showAddEventForm = true">Add Event</button>
      </div>

      <!-- Tab Selector -->
      <div class="tab-selector">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'events' }"
          @click="activeTab = 'events'"
        >
          Events
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'company' }"
          @click="activeTab = 'company'"
        >
          Company Basic
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'report' }"
          @click="activeTab = 'report'"
        >
          Report
        </button>
      </div>

      <!-- Events Tab Content -->
      <div v-if="activeTab === 'events'" class="tab-content">
        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot positive"></span>
            <span>Positive Event</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot negative"></span>
            <span>Negative Event</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot neutral"></span>
            <span>Neutral Event</span>
          </div>
        </div>

        <!-- Event Filters -->
        <div class="event-filters">
        <div class="filter-section">
          <span class="filter-label">Filter by type:</span>
          <div class="filter-buttons">
            <button 
              class="filter-btn" 
              :class="{ active: eventFilters.positive }"
              @click="eventFilters.positive = !eventFilters.positive"
            >
              <span class="filter-dot positive"></span>
              Positive
            </button>
            <button 
              class="filter-btn" 
              :class="{ active: eventFilters.negative }"
              @click="eventFilters.negative = !eventFilters.negative"
            >
              <span class="filter-dot negative"></span>
              Negative
            </button>
            <button 
              class="filter-btn" 
              :class="{ active: eventFilters.neutral }"
              @click="eventFilters.neutral = !eventFilters.neutral"
            >
              <span class="filter-dot neutral"></span>
              Neutral
            </button>
          </div>
        </div>
        <div class="filter-section">
          <span class="filter-label">Filter by category:</span>
          <div class="filter-buttons">
            <button 
              class="filter-btn category-btn" 
              :class="{ active: categoryFilters.macro }"
              @click="categoryFilters.macro = !categoryFilters.macro"
            >
              Macro
            </button>
            <button 
              class="filter-btn category-btn" 
              :class="{ active: categoryFilters.micro }"
              @click="categoryFilters.micro = !categoryFilters.micro"
            >
              Micro
            </button>
            <button 
              class="filter-btn category-btn" 
              :class="{ active: categoryFilters.market }"
              @click="categoryFilters.market = !categoryFilters.market"
            >
              Market
            </button>
            <button 
              class="filter-btn category-btn" 
              :class="{ active: categoryFilters.industry }"
              @click="categoryFilters.industry = !categoryFilters.industry"
            >
              Industry
            </button>
            <button 
              class="filter-btn category-btn" 
              :class="{ active: categoryFilters.product }"
              @click="categoryFilters.product = !categoryFilters.product"
            >
              Product
            </button>
          </div>
        </div>
        <div class="filter-section">
          <span class="filter-label">Filter by status:</span>
          <div class="filter-buttons">
            <button 
              class="filter-btn status-btn" 
              :class="{ active: forecastFilters.actual }"
              @click="forecastFilters.actual = !forecastFilters.actual"
            >
              Actual Events
            </button>
            <button 
              class="filter-btn status-btn" 
              :class="{ active: forecastFilters.forecast }"
              @click="forecastFilters.forecast = !forecastFilters.forecast"
            >
              Forecast Events
            </button>
          </div>
        </div>
        <button 
          class="filter-btn clear-all" 
          @click="clearFilters"
        >
          Show All
        </button>
      </div>

      <div class="events-list">
        <div 
          v-for="event in filteredEvents" 
          :key="event.id" 
          class="event-item"
          :class="event.type"
          @mouseenter="highlightEvent(event)"
          @mouseleave="unhighlightEvent"
        >
          <span class="event-dot" :class="[event.type, { forecast: event.isForecast }]"></span>
          <div class="event-content" :class="{ forecast: event.isForecast }">
            <div class="event-header">
              <h3 class="event-title">
                {{ event.title }}
                <span v-if="event.isForecast" class="forecast-badge">Forecast</span>
              </h3>
              <span class="event-category-badge" :class="event.category">{{ getCategoryLabel(event.category) }}</span>
            </div>
            <p class="event-date">{{ formatDate(event.date) }}</p>
            <p class="event-description">{{ event.description }}</p>
          </div>
        </div>
        <div v-if="filteredEvents.length === 0 && events.length > 0" class="no-events">
          <p>No events match the selected filters.</p>
        </div>
        <div v-if="events.length === 0" class="no-events">
          <p>No events added yet. Click "Add Event" to create one.</p>
        </div>
      </div>
      </div>

      <!-- Company Basic Tab Content (Micro Economics) -->
      <div v-if="activeTab === 'company'" class="tab-content">
        <div class="company-basic-content">
          <div v-if="loadingCompany" class="loading">Loading Company Data...</div>
          <div v-else-if="companyError" class="error">{{ companyError }}</div>
          
          <div v-else-if="companyData" class="company-data">
            <div class="company-header">
              <h3>{{ companyData.company_name }} ({{ companyData.ticker }})</h3>
              <div class="company-price-info">
                <span class="company-price">${{ companyData.price }}</span>
                <span class="company-sector">{{ companyData.sector }} | {{ companyData.industry }}</span>
              </div>
            </div>

            <!-- Micro Economics Tabs -->
            <div class="micro-tabs">
              <button :class="{ active: microTab === 'overview' }" @click="microTab = 'overview'">Overview</button>
              <button :class="{ active: microTab === 'financials' }" @click="microTab = 'financials'">Financial Statements</button>
              <button :class="{ active: microTab === 'ratios' }" @click="microTab = 'ratios'">Ratios</button>
              <button :class="{ active: microTab === 'notes' }" @click="microTab = 'notes'">Notes & Disclosures</button>
              <button :class="{ active: microTab === 'drivers' }" @click="microTab = 'drivers'">Operating Drivers</button>
              <button :class="{ active: microTab === 'capital' }" @click="microTab = 'capital'">Capital Structure</button>
              <button :class="{ active: microTab === 'filings' }" @click="microTab = 'filings'">Filings</button>
              <button :class="{ active: microTab === 'release' }" @click="microTab = 'release'">Release</button>
              <button :class="{ active: microTab === 'holders' }" @click="microTab = 'holders'">Holders</button>
              <button :class="{ active: microTab === 'trading' }" @click="microTab = 'trading'">Trading</button>
            </div>

            <!-- Micro Tab Content -->
            <div class="micro-tab-content">
              <!-- Overview Tab -->
              <div v-if="microTab === 'overview'" class="micro-tab-pane">
                <div class="ai-section">
                  <button @click="generateAllAnalyses" :disabled="analyzing" class="ai-btn">
                    {{ analyzing ? 'Generating Complete Deep Dive...' : '✨ Generate Complete Deep Dive Analysis' }}
                  </button>
                  
                  <div v-if="analyzing" class="progress-indicator">
                    <p>{{ analysisProgress }}</p>
                  </div>
                  
                  <div v-if="analysisReport" class="analysis-section">
                    <h4>Company Overview & Industry Analysis</h4>
                    <div class="report-content" v-html="renderMarkdown(analysisReport)"></div>
                  </div>

                  <div v-if="notesReport" class="analysis-section">
                    <h4>Notes & Disclosures</h4>
                    <div class="report-content" v-html="renderMarkdown(notesReport)"></div>
                  </div>

                  <div v-if="driversReport" class="analysis-section">
                    <h4>Operating Drivers</h4>
                    <div class="report-content" v-html="renderMarkdown(driversReport)"></div>
                    
                    <div v-if="companyData" class="metrics-viz">
                      <h5>Key Operating Metrics (LTM)</h5>
                      <div class="metrics-grid">
                        <div class="metric-card">
                          <div class="metric-label">Revenue Growth</div>
                          <div class="metric-value">{{ calculateRevenueGrowth() }}%</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Operating Margin</div>
                          <div class="metric-value">{{ formatPercentMicro(companyData.ratios?.profitability?.operatingMargins) }}</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Asset Turnover</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.efficiency?.assetTurnover) }}x</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Inventory Turnover</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.efficiency?.inventoryTurnover) }}x</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="capitalReport" class="analysis-section">
                    <h4>Capital Structure & Financing</h4>
                    <div class="report-content" v-html="renderMarkdown(capitalReport)"></div>
                    
                    <div v-if="companyData" class="capital-viz">
                      <h5>Capital Structure Metrics</h5>
                      <div class="metrics-grid">
                        <div class="metric-card">
                          <div class="metric-label">Debt/Equity</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEquity) }}</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Debt/EBITDA</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEbitda) }}x</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Interest Coverage</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.interestCoverage) }}x</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">FCF Yield</div>
                          <div class="metric-value">{{ formatPercentMicro(companyData.ratios?.profitability?.fcfYield) }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Financial Statements Tab -->
              <div v-if="microTab === 'financials'" class="micro-tab-pane">
                <div class="financials-header">
                  <h4>Financial Statements Overview</h4>
                  <div class="period-selector">
                    <button :class="{ active: financialPeriod === 'annual' }" @click="financialPeriod = 'annual'">Annual</button>
                    <button :class="{ active: financialPeriod === 'quarterly' }" @click="financialPeriod = 'quarterly'">Quarterly</button>
                  </div>
                </div>
                
                <h5>LTM Snapshot</h5>
                <div class="financial-summary">
                  <div class="summary-card">
                    <div class="summary-label">Revenue (LTM)</div>
                    <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('income', 'Total Revenue', 'ltm')) }}</div>
                    <div class="summary-change" :class="getRevenueGrowthClass()">{{ calculateRevenueGrowth() }}% YoY</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">Net Income (LTM)</div>
                    <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('income', 'Net Income', 'ltm')) }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">Total Assets</div>
                    <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('balance', 'Total Assets', 'ltm')) }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">Free Cash Flow (LTM)</div>
                    <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('cashflow', 'Free Cash Flow', 'ltm')) }}</div>
                  </div>
                </div>

                <div class="charts-row">
                  <div class="chart-section">
                    <h5>Revenue & Profitability Trends ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</h5>
                    <div class="chart-container">
                      <canvas ref="revenueProfitChart"></canvas>
                    </div>
                  </div>

                  <div class="chart-section">
                    <h5>Cash Flow Analysis ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</h5>
                    <div class="chart-container">
                      <canvas ref="cashflowChart"></canvas>
                    </div>
                  </div>

                  <div class="chart-section">
                    <h5>Balance Sheet Composition (Latest)</h5>
                    <div class="balance-composition">
                      <div class="composition-chart">
                        <h6>Assets</h6>
                        <canvas ref="assetsChart"></canvas>
                      </div>
                      <div class="composition-chart">
                        <h6>Liabilities & Equity</h6>
                        <canvas ref="liabilitiesChart"></canvas>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="detailed-tables">
                  <details>
                    <summary><strong>Income Statement ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</strong></summary>
                    <div class="table-container">
                      <table v-if="getFinancialYears('income', financialPeriod).length > 0">
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th class="ltm-header">LTM</th>
                            <th v-for="period in getFinancialYears('income', financialPeriod)" :key="period">{{ formatPeriodLabel(period) }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in getFinancialItems('income', financialPeriod)" :key="item">
                            <td class="item-name">{{ item }}</td>
                            <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('income', item, 'ltm')) }}</td>
                            <td v-for="period in getFinancialYears('income', financialPeriod)" :key="period">
                              {{ formatFinancialNumber(getFinancialValueByPeriod('income', item, period, financialPeriod)) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </details>

                  <details>
                    <summary><strong>Balance Sheet ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</strong></summary>
                    <div class="table-container">
                      <table v-if="getFinancialYears('balance', financialPeriod).length > 0">
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th class="ltm-header">LTM</th>
                            <th v-for="period in getFinancialYears('balance', financialPeriod)" :key="period">{{ formatPeriodLabel(period) }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in getFinancialItems('balance', financialPeriod)" :key="item">
                            <td class="item-name">{{ item }}</td>
                            <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('balance', item, 'ltm')) }}</td>
                            <td v-for="period in getFinancialYears('balance', financialPeriod)" :key="period">
                              {{ formatFinancialNumber(getFinancialValueByPeriod('balance', item, period, financialPeriod)) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </details>

                  <details>
                    <summary><strong>Cash Flow Statement ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</strong></summary>
                    <div class="table-container">
                      <table v-if="getFinancialYears('cashflow', financialPeriod).length > 0">
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th class="ltm-header">LTM</th>
                            <th v-for="period in getFinancialYears('cashflow', financialPeriod)" :key="period">{{ formatPeriodLabel(period) }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in getFinancialItems('cashflow', financialPeriod)" :key="item">
                            <td class="item-name">{{ item }}</td>
                            <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('cashflow', item, 'ltm')) }}</td>
                            <td v-for="period in getFinancialYears('cashflow', financialPeriod)" :key="period">
                              {{ formatFinancialNumber(getFinancialValueByPeriod('cashflow', item, period, financialPeriod)) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </details>
                </div>
              </div>

              <!-- Ratios Tab -->
              <div v-if="microTab === 'ratios'" class="micro-tab-pane">
                <div class="ratios-grid">
                  <div class="ratio-card">
                    <h5>Profitability</h5>
                    <p>Gross Margin: {{ formatPercentMicro(companyData.ratios?.profitability?.grossMargins) }}</p>
                    <p>Operating Margin: {{ formatPercentMicro(companyData.ratios?.profitability?.operatingMargins) }}</p>
                    <p>EBITDA Margin: {{ formatPercentMicro(companyData.ratios?.profitability?.ebitdaMargins) }}</p>
                    <p>Net Margin: {{ formatPercentMicro(companyData.ratios?.profitability?.netMargin) }}</p>
                    <p>ROA: {{ formatPercentMicro(companyData.ratios?.profitability?.returnOnAssets) }}</p>
                    <p>ROE: {{ formatPercentMicro(companyData.ratios?.profitability?.returnOnEquity) }}</p>
                    <p>ROIC: {{ formatPercentMicro(companyData.ratios?.profitability?.returnOnInvestedCapital) }}</p>
                    <p>FCF Yield: {{ formatPercentMicro(companyData.ratios?.profitability?.fcfYield) }}</p>
                  </div>
                  <div class="ratio-card">
                    <h5>Liquidity & Solvency</h5>
                    <p>Current Ratio: {{ formatRatioMicro(companyData.ratios?.liquidity?.currentRatio) }}</p>
                    <p>Quick Ratio: {{ formatRatioMicro(companyData.ratios?.liquidity?.quickRatio) }}</p>
                    <p>Debt/Equity: {{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEquity) }}</p>
                    <p>Debt/EBITDA: {{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEbitda) }}</p>
                    <p>Interest Coverage: {{ formatRatioMicro(companyData.ratios?.liquidity?.interestCoverage) }}</p>
                  </div>
                  <div class="ratio-card">
                    <h5>Efficiency</h5>
                    <p>Inventory Turnover: {{ formatRatioMicro(companyData.ratios?.efficiency?.inventoryTurnover) }}</p>
                    <p>Days Sales Outstanding: {{ formatDaysMicro(companyData.ratios?.efficiency?.daysSalesOutstanding) }}</p>
                    <p>Days Payable Outstanding: {{ formatDaysMicro(companyData.ratios?.efficiency?.daysPayableOutstanding) }}</p>
                    <p>Asset Turnover: {{ formatRatioMicro(companyData.ratios?.efficiency?.assetTurnover) }}</p>
                    <p>Working Capital: {{ formatNumberMicro(companyData.ratios?.efficiency?.workingCapital) }}</p>
                  </div>
                  <div class="ratio-card">
                    <h5>Valuation</h5>
                    <p>P/E (Trailing): {{ formatRatioMicro(companyData.ratios?.valuation?.trailingPE) }}</p>
                    <p>P/E (Forward): {{ formatRatioMicro(companyData.ratios?.valuation?.forwardPE) }}</p>
                    <p>P/B: {{ formatRatioMicro(companyData.ratios?.valuation?.priceToBook) }}</p>
                    <p>EV/EBITDA: {{ formatRatioMicro(companyData.ratios?.valuation?.enterpriseToEbitda) }}</p>
                    <p>P/S: {{ formatRatioMicro(companyData.ratios?.valuation?.priceToSales) }}</p>
                    <p>EV/Revenue: {{ formatRatioMicro(companyData.ratios?.valuation?.evToRevenue) }}</p>
                  </div>
                </div>
              </div>

              <!-- Notes & Disclosures Tab -->
              <div v-if="microTab === 'notes'" class="micro-tab-pane">
                <div class="ai-section">
                  <button @click="generateNotesAnalysis" :disabled="analyzingNotes" class="ai-btn">
                    {{ analyzingNotes ? 'Generating Analysis...' : '📋 Generate Notes & Disclosures Analysis' }}
                  </button>
                  <div v-if="notesReport" class="report-content" v-html="renderMarkdown(notesReport)"></div>
                  <div v-else class="info-message">
                    Generate the Complete Deep Dive from the Overview tab to see this analysis.
                  </div>
                </div>
              </div>

              <!-- Operating Drivers Tab -->
              <div v-if="microTab === 'drivers'" class="micro-tab-pane">
                <div class="ai-section">
                  <button @click="generateDriversAnalysis" :disabled="analyzingDrivers" class="ai-btn">
                    {{ analyzingDrivers ? 'Generating Analysis...' : '⚙️ Generate Operating Drivers Analysis' }}
                  </button>
                  
                  <div v-if="driversReport">
                    <div class="report-content" v-html="renderMarkdown(driversReport)"></div>
                    
                    <div v-if="companyData" class="metrics-viz">
                      <h5>Key Operating Metrics (LTM)</h5>
                      <div class="metrics-grid">
                        <div class="metric-card">
                          <div class="metric-label">Revenue Growth</div>
                          <div class="metric-value">{{ calculateRevenueGrowth() }}%</div>
                          <div class="metric-trend" :class="calculateRevenueGrowth() > 0 ? 'positive' : 'negative'">
                            {{ calculateRevenueGrowth() > 0 ? '↑' : '↓' }}
                          </div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Operating Margin</div>
                          <div class="metric-value">{{ formatPercentMicro(companyData.ratios?.profitability?.operatingMargins) }}</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Asset Turnover</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.efficiency?.assetTurnover) }}x</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Inventory Turnover</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.efficiency?.inventoryTurnover) }}x</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Days Sales Outstanding</div>
                          <div class="metric-value">{{ formatDaysMicro(companyData.ratios?.efficiency?.daysSalesOutstanding) }}</div>
                        </div>
                        <div class="metric-card">
                          <div class="metric-label">Working Capital</div>
                          <div class="metric-value">{{ formatNumberMicro(companyData.ratios?.efficiency?.workingCapital) }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="info-message">
                    Generate the Complete Deep Dive from the Overview tab to see this analysis.
                  </div>
                </div>
              </div>

              <!-- Capital Structure Tab -->
              <div v-if="microTab === 'capital'" class="micro-tab-pane">
                <div class="ai-section">
                  <button @click="generateCapitalAnalysis" :disabled="analyzingCapital" class="ai-btn">
                    {{ analyzingCapital ? 'Generating Analysis...' : '💰 Generate Capital Structure Analysis' }}
                  </button>
                  
                  <div v-if="capitalReport">
                    <div class="report-content" v-html="renderMarkdown(capitalReport)"></div>
                    
                    <div v-if="companyData" class="capital-viz">
                      <h5>Capital Structure Metrics</h5>
                      <div class="metrics-grid">
                        <div class="metric-card highlight">
                          <div class="metric-label">Debt/Equity</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEquity) }}</div>
                        </div>
                        <div class="metric-card highlight">
                          <div class="metric-label">Debt/EBITDA</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.debtToEbitda) }}x</div>
                        </div>
                        <div class="metric-card highlight">
                          <div class="metric-label">Interest Coverage</div>
                          <div class="metric-value">{{ formatRatioMicro(companyData.ratios?.liquidity?.interestCoverage) }}x</div>
                        </div>
                        <div class="metric-card highlight">
                          <div class="metric-label">FCF Yield</div>
                          <div class="metric-value">{{ formatPercentMicro(companyData.ratios?.profitability?.fcfYield) }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="info-message">
                    Generate the Complete Deep Dive from the Overview tab to see this analysis.
                  </div>
                </div>
              </div>

              <!-- Filings Tab -->
              <div v-if="microTab === 'filings'" class="micro-tab-pane">
                <h4>SEC Filings</h4>
                <div v-if="companyData.filings && companyData.filings.length > 0" class="filings-container">
                  <table class="filings-table">
                    <thead>
                      <tr>
                        <th @click="sortFilings('type')" class="sortable">
                          Filing Type 
                          <span class="sort-icon">{{ getSortIcon('type') }}</span>
                        </th>
                        <th @click="sortFilings('date')" class="sortable">
                          Date 
                          <span class="sort-icon">{{ getSortIcon('date') }}</span>
                        </th>
                        <th>SEC Link</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(filing, index) in sortedFilings" :key="index">
                        <td class="filing-type">{{ filing.type }}</td>
                        <td class="filing-date">{{ formatFilingDate(filing.date) }}</td>
                        <td class="filing-link">
                          <a :href="filing.link" target="_blank" rel="noopener noreferrer">
                            View on SEC.gov →
                          </a>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="no-data">No SEC filings data available</div>
              </div>

              <!-- Release Tab (Key Logs) -->
              <div v-if="microTab === 'release'" class="micro-tab-pane">
                <h4>Key Logs - Releases</h4>
                <div v-if="companyData.releases && companyData.releases.length > 0" class="filings-container">
                  <table class="filings-table">
                    <thead>
                      <tr>
                        <th @click="sortReleases('type')" class="sortable">
                          Release Type 
                          <span class="sort-icon">{{ getReleaseSortIcon('type') }}</span>
                        </th>
                        <th @click="sortReleases('date')" class="sortable">
                          Date 
                          <span class="sort-icon">{{ getReleaseSortIcon('date') }}</span>
                        </th>
                        <th>Title</th>
                        <th>Link</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(release, index) in sortedReleases" :key="index">
                        <td class="filing-type">{{ release.type || 'Press Release' }}</td>
                        <td class="filing-date">{{ formatFilingDate(release.date) }}</td>
                        <td class="filing-title">{{ release.title || release.headline || 'N/A' }}</td>
                        <td class="filing-link">
                          <a v-if="release.link" :href="release.link" target="_blank" rel="noopener noreferrer">
                            View Release →
                          </a>
                          <span v-else class="no-link">N/A</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="no-data">No release data available</div>
              </div>

              <!-- Holders Tab -->
              <div v-if="microTab === 'holders'" class="micro-tab-pane">
                <h4>Trade Log</h4>
                
                <div class="trade-log-tabs">
                  <button :class="{ active: holdersView === 'all' }" @click="holdersView = 'all'">All</button>
                  <button :class="{ active: holdersView === 'institutions' }" @click="holdersView = 'institutions'">Institutions</button>
                  <button :class="{ active: holdersView === 'insider' }" @click="holdersView = 'insider'">Insider</button>
                </div>

                <div v-if="holdersView === 'insider' || holdersView === 'all'" class="trade-log-container">
                  <h5 v-if="holdersView === 'all'" class="section-heading">Insider Transactions</h5>
                  <table class="trade-log-table" v-if="getInsiderTransactions().length > 0">
                    <thead>
                      <tr>
                        <th>DATE</th>
                        <th>ACTION</th>
                        <th>SHARE</th>
                        <th>SHARE VALUE</th>
                        <th>HOLDING</th>
                        <th>PARTY</th>
                        <th>INSIDER</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(transaction, index) in getInsiderTransactions()" :key="index">
                        <td class="trade-date">{{ formatTradeDate(transaction['Start Date']) }}</td>
                        <td class="trade-action" :class="getActionClass(transaction.Text)">
                          {{ extractAction(transaction.Text) }}
                        </td>
                        <td class="trade-shares">{{ formatNumberMicro(transaction.Shares) }}</td>
                        <td class="trade-value">{{ formatNumberMicro(transaction.Value) }}</td>
                        <td class="trade-holdings">{{ transaction.Ownership }}</td>
                        <td class="trade-party">{{ transaction.Position || 'Officer' }}</td>
                        <td class="trade-insider">{{ transaction.Insider }}</td>
                      </tr>
                    </tbody>
                  </table>
                  <div v-else class="no-data">No insider transaction data available</div>
                </div>

                <div v-if="holdersView === 'institutions' || holdersView === 'all'" class="trade-log-container">
                  <h5 v-if="holdersView === 'all'" class="section-heading">Institutional Holders</h5>
                  <table class="trade-log-table" v-if="getInstitutionalHolders().length > 0">
                    <thead>
                      <tr>
                        <th>DATE REPORTED</th>
                        <th>HOLDER</th>
                        <th>SHARES</th>
                        <th>VALUE</th>
                        <th>% HELD</th>
                        <th>% CHANGE</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(holder, index) in getInstitutionalHolders()" :key="index">
                        <td class="trade-date">{{ formatTradeDate(holder['Date Reported']) }}</td>
                        <td class="trade-insider">{{ holder.Holder }}</td>
                        <td class="trade-shares">{{ formatNumberMicro(holder.Shares) }}</td>
                        <td class="trade-value">{{ formatCurrencyMicro(holder.Value) }}</td>
                        <td class="trade-holdings">{{ formatPercentMicro(holder.pctHeld) }}</td>
                        <td class="trade-action" :class="getChangeClass(holder.pctChange)">
                          {{ formatPercentChange(holder.pctChange) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <div v-else class="no-data">No institutional holder data available</div>
                </div>
              </div>

              <!-- Trading Tab -->
              <div v-if="microTab === 'trading'" class="micro-tab-pane">
                <div class="ratios-grid">
                  <div class="ratio-card">
                    <h5>Short Interest</h5>
                    <p>Short Ratio: {{ companyData.trading?.shortRatio }}</p>
                    <p>Short % of Float: {{ formatPercentMicro(companyData.trading?.shortPercentOfFloat) }}</p>
                    <p>Shares Short: {{ formatNumberMicro(companyData.trading?.sharesShort) }}</p>
                  </div>
                  <div class="ratio-card">
                    <h5>Volume & Price</h5>
                    <p>Avg Volume: {{ formatNumberMicro(companyData.trading?.averageVolume) }}</p>
                    <p>52W High: ${{ companyData.trading?.fiftyTwoWeekHigh }}</p>
                    <p>52W Low: ${{ companyData.trading?.fiftyTwoWeekLow }}</p>
                    <p>Beta: {{ companyData.trading?.beta }}</p>
                  </div>
                </div>
                
                <div v-if="companyData.trading?.options && companyData.trading.options.length > 0" class="options-charts-container">
                  <div class="options-chart-section">
                    <h5>Total Volume & Open Interest by Expiry Date</h5>
                    <div class="chart-container">
                      <canvas ref="optionsVolumeChart"></canvas>
                    </div>
                  </div>
                  
                  <div class="options-chart-section">
                    <h5>Calls & Puts Volume by Expiry Date</h5>
                    <div class="chart-container">
                      <canvas ref="optionsCallsPutsChart"></canvas>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-company-data">
            <p>Select a stock from the dropdown above to view company information.</p>
          </div>
        </div>
      </div>

      <!-- Report Tab Content -->
      <div v-if="activeTab === 'report'" class="tab-content report-tab-content">
        <div class="report-container">
          <!-- Main Report Area -->
          <div class="main-report-area">
            <div class="upload-section" v-if="!report">
              <h3>Upload Document (PDF/HTML)</h3>
              <input type="file" @change="handleFileUpload" :disabled="loadingReport" />
            </div>
            
            <div v-if="loadingReport" class="loading">
              <p>{{ reportStatusMessage }}</p>
            </div>
            
            <div v-else-if="reportError" class="error">{{ reportError }}</div>
            
            <!-- Generated Report (Immediate) -->
            <div class="report-content" v-if="report">
              <h3>Generated Report</h3>
              <div class="report-body" v-html="formattedReport"></div>
            </div>
          </div>

          <!-- Sidebar for Saved Reports (Right Side) -->
          <div class="reports-sidebar">
            <h3>Saved Reports</h3>
            <div v-if="loadingReports" class="loading-small">Loading...</div>
            <div v-else-if="savedReports.length === 0" class="no-reports">No saved reports</div>
            <ul v-else class="report-list">
              <li v-for="savedReport in savedReports" :key="savedReport.id" @click="selectReport(savedReport)" :class="{ active: selectedReportId === savedReport.id }">
                <span class="report-ticker">{{ savedReport.ticker || savedReport.title }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Modal for Viewing Reports -->
        <div v-if="showReportModal" class="modal-overlay" @click="closeReportModal">
          <div class="modal-content" @click.stop>
            <div class="modal-header">
              <h3>{{ selectedReportTitle }}</h3>
              <button @click="closeReportModal" class="close-btn">Close</button>
            </div>
            <div class="modal-body">
              <div v-if="loadingModal" class="loading">Loading report...</div>
              <div v-else class="report-body" v-html="formattedModalReport"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Event Modal -->
    <div v-if="showAddEventForm" class="modal-overlay" @click.self="closeAddEventForm">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Add New Event</h3>
          <button class="close-btn" @click="closeAddEventForm">&times;</button>
        </div>
        <form @submit.prevent="addEvent" class="event-form">
          <div class="form-group">
            <label for="event-date">Date *</label>
            <input 
              type="date" 
              id="event-date" 
              v-model="newEvent.date" 
              required
              :max="maxDate"
            />
          </div>
          <div class="form-group">
            <label for="event-title">Title *</label>
            <input 
              type="text" 
              id="event-title" 
              v-model="newEvent.title" 
              required
              placeholder="e.g., Q4 2023 Earnings Miss"
            />
          </div>
          <div class="form-group">
            <label for="event-description">Description *</label>
            <textarea 
              id="event-description" 
              v-model="newEvent.description" 
              required
              rows="3"
              placeholder="e.g., Tesla reported lower-than-expected Q4 earnings, causing stock decline."
            ></textarea>
          </div>
          <div class="form-group">
            <label for="event-type">Event Type *</label>
            <select id="event-type" v-model="newEvent.type" required>
              <option value="positive">Positive Event</option>
              <option value="negative">Negative Event</option>
              <option value="neutral">Neutral Event</option>
            </select>
          </div>
          <div class="form-group">
            <label for="event-category">Category *</label>
            <select id="event-category" v-model="newEvent.category" required>
              <option value="macro">Macro - FED decisions, policy changes, economic indicators</option>
              <option value="micro">Micro - Company-specific internal events</option>
              <option value="market">Market - Trading and financial events</option>
              <option value="industry">Industry - Sector-wide events</option>
              <option value="product">Product - Product-related announcements</option>
            </select>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="newEvent.isForecast"
              />
              <span>Mark as Forecast Event (for upcoming expected events)</span>
            </label>
            <p class="form-hint">Forecast events are for scheduled future events like earnings reports, product launches, or regulatory decisions.</p>
          </div>
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeAddEventForm">Cancel</button>
            <button type="submit" class="submit-btn">Add Event</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  DoughnutController,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

// Register additional Chart.js components for Micro Economics
ChartJS.register(
  BarElement,
  ArcElement,
  DoughnutController
)

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

// Stock data
const selectedStock = ref('TSLA')
const stockSearchInput = ref('TSLA')
const timelineYear = ref('2024')
const referenceDate = ref('Jan 2024')
const currentPrice = ref(352.56)
const priceChange = ref(104.14)
const priceChangePercent = ref(41.92)
const loadingStock = ref(false)
const stockError = ref(null)

// Time period selector
const selectedTimePeriod = ref('max')
const timePeriods = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Yearly', value: 'yearly' },
  { label: 'Max', value: 'max' }
]

// Events
const events = ref([
  {
    id: 1,
    date: '2024-01-31',
    title: 'Q4 2023 Earnings Miss',
    description: 'Tesla reported lower-than-expected Q4 earnings, causing stock decline.',
    type: 'negative',
    category: 'market',
    isForecast: false
  },
  {
    id: 2,
    date: '2024-03-31',
    title: 'Price Cuts Announced',
    description: 'Tesla announced price cuts across multiple vehicle models globally.',
    type: 'negative',
    category: 'product',
    isForecast: false
  },
  {
    id: 3,
    date: '2024-06-30',
    title: 'Robotaxi Announcement',
    description: 'Elon Musk announced plans for Tesla Robotaxi unveiling, boosting investor confidence.',
    type: 'positive',
    category: 'product',
    isForecast: false
  },
  {
    id: 4,
    date: '2024-08-31',
    title: 'Record Deliveries',
    description: 'Tesla reported record quarterly deliveries beating analyst expectations.',
    type: 'positive',
    category: 'market',
    isForecast: false
  },
  {
    id: 5,
    date: '2024-10-31',
    title: 'Cybertruck Production Ramp',
    description: 'Tesla announced significant Cybertruck production increases.',
    type: 'positive',
    category: 'product',
    isForecast: false
  },
  // Forecast Events
  {
    id: 6,
    date: '2025-01-15',
    title: 'Q4 2024 Earnings Report',
    description: 'Scheduled Q4 2024 earnings release. Analysts expect strong performance driven by record deliveries.',
    type: 'positive',
    category: 'market',
    isForecast: true
  },
  {
    id: 7,
    date: '2025-02-20',
    title: 'Model Y Refresh Launch',
    description: 'Expected announcement of refreshed Model Y with new features and improved range.',
    type: 'positive',
    category: 'product',
    isForecast: true
  },
  {
    id: 8,
    date: '2025-03-15',
    title: 'FED Interest Rate Decision',
    description: 'Federal Reserve meeting to decide on interest rates. Potential impact on auto financing and consumer spending.',
    type: 'neutral',
    category: 'macro',
    isForecast: true
  },
  {
    id: 9,
    date: '2025-04-10',
    title: 'Q1 2025 Earnings Report',
    description: 'Scheduled Q1 2025 earnings release. Market will be watching for delivery guidance and margin improvements.',
    type: 'positive',
    category: 'market',
    isForecast: true
  },
  {
    id: 10,
    date: '2025-05-05',
    title: 'New Gigafactory Announcement',
    description: 'Expected announcement of new Gigafactory location to expand production capacity.',
    type: 'positive',
    category: 'industry',
    isForecast: true
  },
  {
    id: 11,
    date: '2025-06-20',
    title: 'FSD Beta Regulatory Review',
    description: 'Regulatory review of Full Self-Driving Beta program. Potential approval or restrictions.',
    type: 'neutral',
    category: 'macro',
    isForecast: true
  },
  {
    id: 12,
    date: '2025-07-15',
    title: 'Competitor EV Launch',
    description: 'Major competitor expected to launch new electric vehicle model, potentially impacting market share.',
    type: 'negative',
    category: 'industry',
    isForecast: true
  },
  {
    id: 13,
    date: '2025-12-25',
    title: 'Holiday Season Sales Report',
    description: 'Expected release of Q4 holiday season sales performance and delivery numbers.',
    type: 'positive',
    category: 'market',
    isForecast: true
  }
])

const showAddEventForm = ref(false)
const highlightedEventId = ref(null)

// Active tab state
const activeTab = ref('events')

// Company Basic / Micro Economics data
const companyData = ref(null)
const loadingCompany = ref(false)
const companyError = ref(null)

// Micro Economics tab state
const microTab = ref('overview')
const financialPeriod = ref('annual')

// Analysis state
const analyzing = ref(false)
const analysisReport = ref(null)
const analyzingNotes = ref(false)
const notesReport = ref(null)
const analyzingDrivers = ref(false)
const driversReport = ref(null)
const analyzingCapital = ref(false)
const capitalReport = ref(null)
const analysisProgress = ref('')

// Report Tab State (from ReportView)
const report = ref('')
const loadingReport = ref(false)
const reportError = ref(null)
const reportStatusMessage = ref('')
const savedReports = ref([])
const loadingReports = ref(false)
const selectedReportId = ref(null)
const selectedReportTitle = ref('')
const showReportModal = ref(false)
const modalReportContent = ref('')
const loadingModal = ref(false)

// Chart refs for Micro Economics
const revenueProfitChart = ref(null)
const cashflowChart = ref(null)
const assetsChart = ref(null)
const liabilitiesChart = ref(null)
const optionsVolumeChart = ref(null)
const optionsCallsPutsChart = ref(null)

// Chart instances
let revenueProfitChartInstance = null
let cashflowChartInstance = null
let assetsChartInstance = null
let liabilitiesChartInstance = null
let optionsVolumeChartInstance = null
let optionsCallsPutsChartInstance = null

// Filings sorting
const filingsSortBy = ref('date')
const filingsSortOrder = ref('desc')

// Releases sorting
const releasesSortBy = ref('date')
const releasesSortOrder = ref('desc')

// Holders view
const holdersView = ref('all')

// Event filters - default: positive and negative selected, neutral deselected
const eventFilters = ref({
  positive: true,
  negative: true,
  neutral: false
})

// Category filters
const categoryFilters = ref({
  macro: true,
  micro: true,
  market: true,
  industry: true,
  product: true
})

// Forecast filters
const forecastFilters = ref({
  actual: true,
  forecast: true
})

const newEvent = ref({
  date: '',
  title: '',
  description: '',
  type: 'neutral',
  category: 'market',
  isForecast: false
})

// Generate mock stock price data (kept for fallback, but not used when real data is available)
const generateStockData = () => {
  const startDate = new Date('2023-12-01')
  // Extend to cover forecast events (through December 2025)
  const endDate = new Date('2025-12-31')
  const data = []
  const prices = []
  
  let stockPrice = 240
  const basePrice = stockPrice
  
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    // Skip weekends
    if (d.getDay() === 0 || d.getDay() === 6) continue
    
    // Add some volatility
    const change = (Math.random() - 0.5) * 5
    stockPrice = Math.max(150, Math.min(380, stockPrice + change))
    
    // Apply event impacts (check if event is on this date or within 1 day)
    const eventDate = new Date(d.toISOString().split('T')[0])
    const event = events.value.find(e => {
      const eDate = new Date(e.date)
      eDate.setHours(0, 0, 0, 0)
      const diff = Math.abs(eDate.getTime() - eventDate.getTime())
      return diff <= 1 * 24 * 60 * 60 * 1000 // Within 1 day
    })
    
    if (event) {
      if (event.type === 'positive') {
        stockPrice += 15 + Math.random() * 10
      } else if (event.type === 'negative') {
        stockPrice -= 15 + Math.random() * 10
      }
    }
    
    data.push({
      date: new Date(d),
      price: stockPrice
    })
    prices.push(stockPrice)
  }
  
  // Update current price
  if (prices.length > 0) {
    currentPrice.value = prices[prices.length - 1]
    const janPrice = prices.find((p, i) => {
      const date = data[i].date
      return date.getMonth() === 0 && date.getDate() === 1
    }) || prices[0]
    priceChange.value = currentPrice.value - janPrice
    priceChangePercent.value = ((priceChange.value / janPrice) * 100)
  }
  
  return data
}

const stockData = ref([]) // Will be populated with real data from API

// Filter stock data based on selected time period
const filteredStockData = computed(() => {
  const allData = stockData.value
  
  // Return empty array if no data
  if (!allData || allData.length === 0) {
    return []
  }
  
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  let startDate = new Date()
  
  switch (selectedTimePeriod.value) {
    case 'daily':
      // Last 30 days
      startDate.setDate(today.getDate() - 30)
      break
    case 'weekly':
      // Last 12 weeks (3 months)
      startDate.setDate(today.getDate() - 84)
      break
    case 'monthly':
      // Last 12 months
      startDate.setMonth(today.getMonth() - 12)
      break
    case 'yearly':
      // Last 5 years
      startDate.setFullYear(today.getFullYear() - 5)
      break
    case 'max':
    default:
      // All data
      return allData
  }
  
  startDate.setHours(0, 0, 0, 0)
  return allData.filter(d => {
    const dataDate = new Date(d.date)
    dataDate.setHours(0, 0, 0, 0)
    return dataDate >= startDate
  })
})

// Chart data
const chartData = computed(() => {
  const dataToUse = filteredStockData.value
  
  // Return empty chart data if no stock data
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
  
  // Adjust label format based on time period
  const labels = dataToUse.map((d, index) => {
    const date = new Date(d.date)
    
    if (selectedTimePeriod.value === 'daily') {
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      return `${month} ${day}`
    } else if (selectedTimePeriod.value === 'weekly') {
      // Show week number or date
      if (index % 7 === 0 || index === 0) {
        const month = date.toLocaleString('default', { month: 'short' })
        const day = date.getDate()
        return `${month} ${day}`
      }
      return ''
    } else if (selectedTimePeriod.value === 'monthly') {
      // Show first of each month
      if (date.getDate() === 1 || index === 0) {
        const month = date.toLocaleString('default', { month: 'short' })
        const year = date.getFullYear()
        return `${month} ${year}`
      }
      return ''
    } else if (selectedTimePeriod.value === 'yearly') {
      // Show first of each year
      if ((date.getMonth() === 0 && date.getDate() === 1) || index === 0) {
        return date.getFullYear().toString()
      }
      return ''
    } else {
      // Max - show monthly labels
      if (date.getDate() === 1 || index === 0 || index === dataToUse.length - 1) {
        const month = date.toLocaleString('default', { month: 'short' })
        const year = date.getFullYear()
        return `${month} ${year}`
      }
      return ''
    }
  })
  
  const prices = dataToUse.map(d => d.price)
  
  // Create event marker datasets
  // For each event type, create an array where most values are null
  // and only event dates have the price value
  // Note: Forecast events are NOT shown on the chart, only actual events
  const createEventDataset = (eventType, color) => {
    const data = new Array(dataToUse.length).fill(null)
    // Only include events that match type and category filters
    // Exclude forecast events from chart
    if (!eventFilters.value[eventType]) {
      return data
    }
    
    events.value.forEach(event => {
      // Only show actual events on chart, skip forecast events
      if (event.isForecast) {
        return
      }
      
      const matchesForecast = forecastFilters.value.actual
      if (event.type === eventType && 
          categoryFilters.value[event.category] && 
          matchesForecast) {
        // Parse event date - handle both string and Date object
        let eventDate
        if (typeof event.date === 'string') {
          eventDate = new Date(event.date + 'T00:00:00')
        } else {
          eventDate = new Date(event.date)
        }
        eventDate.setHours(0, 0, 0, 0)
        
        // Find the closest trading day in filtered data
        let closestIndex = -1
        let minDiff = Infinity
        
        dataToUse.forEach((d, index) => {
          // Handle both Date objects and date strings
          let dDate
          if (d.date instanceof Date) {
            dDate = new Date(d.date)
          } else {
            dDate = new Date(d.date)
          }
          dDate.setHours(0, 0, 0, 0)
          const diff = Math.abs(dDate.getTime() - eventDate.getTime())
          // First try to find within 5 days
          if (diff < minDiff && diff <= 5 * 24 * 60 * 60 * 1000) {
            minDiff = diff
            closestIndex = index
          }
        })
        
        // If no match found within 5 days, find the closest date overall
        if (closestIndex === -1 && dataToUse.length > 0) {
          minDiff = Infinity
          dataToUse.forEach((d, index) => {
            let dDate
            if (d.date instanceof Date) {
              dDate = new Date(d.date)
            } else {
              dDate = new Date(d.date)
            }
            dDate.setHours(0, 0, 0, 0)
            const diff = Math.abs(dDate.getTime() - eventDate.getTime())
            if (diff < minDiff) {
              minDiff = diff
              closestIndex = index
            }
          })
        }
        
        if (closestIndex !== -1 && closestIndex < dataToUse.length) {
          data[closestIndex] = dataToUse[closestIndex].price
        }
      }
    })
    return data
  }
  
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
  
  // Add event marker datasets (only actual events, forecast events are not shown on chart)
  const positiveData = createEventDataset('positive', '#42b983')
  const negativeData = createEventDataset('negative', '#e74c3c')
  const neutralData = createEventDataset('neutral', '#95a5a6')
  
  // Actual events only
  if (positiveData.some(v => v !== null)) {
    datasets.push({
      label: 'Positive Events',
      data: positiveData,
      backgroundColor: '#42b983',
      borderColor: '#42b983',
      pointRadius: 6,
      pointHoverRadius: 8,
      showLine: false,
      pointStyle: 'circle'
    })
  }
  
  if (negativeData.some(v => v !== null)) {
    datasets.push({
      label: 'Negative Events',
      data: negativeData,
      backgroundColor: '#e74c3c',
      borderColor: '#e74c3c',
      pointRadius: 6,
      pointHoverRadius: 8,
      showLine: false,
      pointStyle: 'circle'
    })
  }
  
  if (neutralData.some(v => v !== null)) {
    datasets.push({
      label: 'Neutral Events',
      data: neutralData,
      backgroundColor: '#95a5a6',
      borderColor: '#95a5a6',
      pointRadius: 6,
      pointHoverRadius: 8,
      showLine: false,
      pointStyle: 'circle'
    })
  }
  
  return {
    labels,
    datasets
  }
})

const chartOptions = computed(() => {
  const dataToUse = filteredStockData.value
  
  // Create a mapping of event data points (only for filtered actual events, forecast events excluded)
  const eventMap = new Map()
  events.value.forEach(event => {
    // Skip forecast events - they don't appear on chart
    if (event.isForecast) {
      return
    }
    
    // Only include actual events that match type, category, and forecast filters
    const matchesForecast = forecastFilters.value.actual
    if (!eventFilters.value[event.type] || !categoryFilters.value[event.category] || !matchesForecast) {
      return
    }
    
    const eventDate = new Date(event.date + 'T00:00:00')
    eventDate.setHours(0, 0, 0, 0)
    
    // Find the closest trading day in filtered data
    let closestIndex = -1
    let minDiff = Infinity
    
    dataToUse.forEach((d, index) => {
      const dDate = new Date(d.date)
      dDate.setHours(0, 0, 0, 0)
      const diff = Math.abs(dDate.getTime() - eventDate.getTime())
      if (diff < minDiff && diff <= 5 * 24 * 60 * 60 * 1000) { // Within 5 days
        minDiff = diff
        closestIndex = index
      }
    })
    
    // If no match found within 5 days, find the closest overall
    if (closestIndex === -1 && dataToUse.length > 0) {
      dataToUse.forEach((d, index) => {
        const dDate = new Date(d.date)
        dDate.setHours(0, 0, 0, 0)
        const diff = Math.abs(dDate.getTime() - eventDate.getTime())
        if (diff < minDiff) {
          minDiff = diff
          closestIndex = index
        }
      })
    }
    
    if (closestIndex !== -1) {
      eventMap.set(closestIndex, event)
    }
  })

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
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        callbacks: {
          title: function(context) {
            return context[0].label
          },
          label: function(context) {
            if (context.datasetIndex === 0) {
              return `Price: $${context.parsed.y.toFixed(2)}`
            } else {
              // This is an event marker
              const dataIndex = context.dataIndex
              const event = eventMap.get(dataIndex)
              if (event) {
                return [
                  event.title,
                  formatDate(event.date),
                  event.description
                ]
              }
            }
            return null
          },
          labelColor: function(context) {
            if (context.datasetIndex > 0) {
              const dataIndex = context.dataIndex
              const event = eventMap.get(dataIndex)
              if (event) {
                const colors = {
                  positive: '#42b983',
                  negative: '#e74c3c',
                  neutral: '#95a5a6'
                }
                return {
                  borderColor: colors[event.type] || '#95a5a6',
                  backgroundColor: colors[event.type] || '#95a5a6'
                }
              }
            }
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
          maxTicksLimit: selectedTimePeriod.value === 'daily' ? 30 : 
                         selectedTimePeriod.value === 'weekly' ? 12 :
                         selectedTimePeriod.value === 'monthly' ? 12 :
                         selectedTimePeriod.value === 'yearly' ? 5 : 20,
          callback: function(value, index) {
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

// Function to check if an event should be converted from forecast to actual
const updateForecastEvents = () => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let hasChanges = false
  
  events.value.forEach(event => {
    if (event.isForecast) {
      const eventDate = new Date(event.date)
      eventDate.setHours(0, 0, 0, 0)
      
      // If current date has passed the event date, convert to actual
      if (today >= eventDate) {
        event.isForecast = false
        hasChanges = true
      }
    }
  })
  
  return hasChanges
}

// Watch for date changes and update forecast events
const checkForecastEvents = () => {
  const changed = updateForecastEvents()
  if (changed) {
    // Force reactivity update
    events.value = [...events.value]
  }
}

// Check forecast events periodically (every minute)
let forecastCheckInterval = null

const sortedEvents = computed(() => {
  return [...events.value].sort((a, b) => new Date(a.date) - new Date(b.date))
})

const filteredEvents = computed(() => {
  return sortedEvents.value.filter(event => {
    const matchesType = eventFilters.value[event.type]
    const matchesCategory = categoryFilters.value[event.category]
    const matchesForecast = event.isForecast ? forecastFilters.value.forecast : forecastFilters.value.actual
    return matchesType && matchesCategory && matchesForecast
  })
})

const clearFilters = () => {
  eventFilters.value = {
    positive: true,
    negative: true,
    neutral: false
  }
  categoryFilters.value = {
    macro: true,
    micro: true,
    market: true,
    industry: true,
    product: true
  }
  forecastFilters.value = {
    actual: true,
    forecast: true
  }
}

const getCategoryLabel = (category) => {
  const labels = {
    macro: 'Macro',
    micro: 'Micro',
    market: 'Market',
    industry: 'Industry',
    product: 'Product'
  }
  return labels[category] || category
}

const maxDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  })
}

const loadStockData = async () => {
  if (!selectedStock.value) return
  
  loadingStock.value = true
  stockError.value = null
  
  try {
    // Determine period based on selected time period
    const periodMap = {
      'daily': '1mo',
      'weekly': '3mo',
      'monthly': '1y',
      'yearly': '2y',
      'max': 'max'
    }
    const period = periodMap[selectedTimePeriod.value] || '2y'
    
    const response = await fetch(`http://localhost:8000/api/internal/stock/${selectedStock.value.toUpperCase()}/history?period=${period}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch stock data' }))
      throw new Error(errorData.detail || 'Failed to fetch stock data')
    }
    
    const data = await response.json()
    
    // Convert API response to chart data format
    stockData.value = data.history.map(item => ({
      date: new Date(item.date + 'T00:00:00'),
      price: item.price
    }))
    
    // Update price info
    currentPrice.value = data.current_price
    priceChange.value = data.price_change
    priceChangePercent.value = data.price_change_percent
    referenceDate.value = data.reference_date
    timelineYear.value = new Date().getFullYear().toString()
    
  } catch (err) {
    stockError.value = err.message || 'Error loading stock data'
    console.error('Error loading stock data:', err)
    // Fallback to empty data
    stockData.value = []
  } finally {
    loadingStock.value = false
  }
}

const searchStock = () => {
  const ticker = stockSearchInput.value.trim().toUpperCase()
  if (!ticker) {
    stockError.value = 'Please enter a ticker symbol'
    return
  }
  
  selectedStock.value = ticker
  loadStockData()
  
  // Also fetch company data if on company tab
  if (activeTab.value === 'company') {
    fetchCompanyData()
  }
}

const fetchCompanyData = async () => {
  if (!selectedStock.value) return
  loadingCompany.value = true
  companyError.value = null
  companyData.value = null
  analysisReport.value = null
  notesReport.value = null
  driversReport.value = null
  capitalReport.value = null
  
  try {
    const response = await fetch(`http://localhost:8000/api/internal/micro/${selectedStock.value.toUpperCase()}`)
    if (!response.ok) throw new Error('Failed to fetch company data')
    companyData.value = await response.json()
    
    // Render charts if on financials or trading tab
    await nextTick()
    if (microTab.value === 'financials') {
      renderFinancialCharts()
    }
    if (microTab.value === 'trading') {
      renderOptionsVolumeChart()
      renderOptionsCallsPutsChart()
    }
  } catch (err) {
    companyError.value = err.message
  } finally {
    loadingCompany.value = false
  }
}

// Watch selectedStock to auto-fetch company data
watch(selectedStock, () => {
  if (activeTab.value === 'company') {
    fetchCompanyData()
  }
})

// Watch activeTab to fetch company data when switching to company tab
watch(activeTab, (newTab) => {
  if (newTab === 'company' && selectedStock.value && !companyData.value) {
    fetchCompanyData()
  }
})

// Watch microTab to render charts when switching tabs
watch([microTab, financialPeriod], async () => {
  if (companyData.value && microTab.value === 'financials') {
    await nextTick()
    renderFinancialCharts()
  }
  if (companyData.value && microTab.value === 'trading') {
    await nextTick()
    renderOptionsVolumeChart()
    renderOptionsCallsPutsChart()
  }
})

// Formatting functions for timeline events
const formatNumber = (value) => {
  if (!value && value !== 0) return 'N/A'
  if (value >= 1e12) return (value / 1e12).toFixed(2) + 'T'
  if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B'
  if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M'
  if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K'
  return value.toFixed(2)
}

const formatRatio = (value) => {
  if (!value && value !== 0) return 'N/A'
  return value.toFixed(2)
}

const formatPercent = (value) => {
  if (!value && value !== 0) return 'N/A'
  return (value * 100).toFixed(2) + '%'
}

// Formatting functions for Micro Economics (matching MicroView)
const formatNumberMicro = (num) => {
  if (!num && num !== 0) return '-'
  if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B'
  if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M'
  if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K'
  return num.toLocaleString()
}

const formatPercentMicro = (num) => {
  if (!num && num !== 0) return '-'
  if (num > 1 || num < -1) return num.toFixed(2) + '%'
  return (num * 100).toFixed(2) + '%'
}

const formatRatioMicro = (num) => {
  if (!num && num !== 0) return '-'
  return num.toFixed(2)
}

const formatDaysMicro = (num) => {
  if (!num && num !== 0) return '-'
  return num.toFixed(0) + ' days'
}

const formatCurrencyMicro = (value) => {
  if (value === null || value === undefined) return '-'
  const absVal = Math.abs(value)
  if (absVal >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B'
  if (absVal >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M'
  if (absVal >= 1e3) return '$' + (value / 1e3).toFixed(2) + 'K'
  return '$' + value.toFixed(2)
}

const formatFinancialNumber = (num) => {
  if (num === null || num === undefined || isNaN(num)) return '-'
  if (num === 0) return '0'
  
  const absNum = Math.abs(num)
  const sign = num < 0 ? '-' : ''
  
  if (absNum >= 1e9) return sign + (absNum / 1e9).toFixed(2) + 'B'
  if (absNum >= 1e6) return sign + (absNum / 1e6).toFixed(2) + 'M'
  if (absNum >= 1e3) return sign + (absNum / 1e3).toFixed(2) + 'K'
  return sign + absNum.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const addEvent = () => {
  if (!newEvent.value.date || !newEvent.value.title || !newEvent.value.description) {
    return
  }
  
  const event = {
    id: Date.now(),
    date: newEvent.value.date,
    title: newEvent.value.title,
    description: newEvent.value.description,
    type: newEvent.value.type,
    category: newEvent.value.category,
    isForecast: newEvent.value.isForecast || false
  }
  
  events.value.push(event)
  
  // Regenerate stock data to reflect event impact
  stockData.value = generateStockData()
  
  // Force reactivity update
  events.value = [...events.value]
  
  // Reset form
  newEvent.value = {
    date: '',
    title: '',
    description: '',
    type: 'neutral',
    category: 'market',
    isForecast: false
  }
  
  showAddEventForm.value = false
}

const closeAddEventForm = () => {
  showAddEventForm.value = false
  newEvent.value = {
    date: '',
    title: '',
    description: '',
    type: 'neutral',
    category: 'market',
    isForecast: false
  }
}

const highlightEvent = (event) => {
  highlightedEventId.value = event.id
}

const unhighlightEvent = () => {
  highlightedEventId.value = null
}

// Micro Economics functions
const calculateRevenueGrowth = () => {
  if (!companyData.value || !companyData.value.financials || !companyData.value.financials.annual) return '-'
  try {
    const revenues = Object.values(companyData.value.financials.annual['Total Revenue'] || {})
    if (revenues.length < 2) return '-'
    const latest = revenues[0]
    const previous = revenues[1]
    if (!latest || !previous) return '-'
    const growth = ((latest - previous) / previous) * 100
    return growth.toFixed(2)
  } catch {
    return '-'
  }
}

const getFinancialYears = (statementType, period = 'annual') => {
  if (!companyData.value) return []
  
  let statement
  if (statementType === 'income') statement = companyData.value.financials
  else if (statementType === 'balance') statement = companyData.value.balance_sheet
  else if (statementType === 'cashflow') statement = companyData.value.cashflow
  
  if (!statement) return []
  
  const dataSource = period === 'annual' ? statement.annual : statement.quarterly
  if (!dataSource) return []
  
  const firstItem = Object.values(dataSource)[0]
  if (!firstItem) return []
  
  const periods = Object.keys(firstItem)
    .map(key => {
      try {
        return new Date(key)
      } catch {
        return null
      }
    })
    .filter(date => date !== null)
    .sort((a, b) => b - a)
  
  return [...new Set(periods.map(d => d.getTime()))]
}

const getFinancialItems = (statementType, period = 'annual') => {
  if (!companyData.value) return []
  
  let statement
  if (statementType === 'income') statement = companyData.value.financials
  else if (statementType === 'balance') statement = companyData.value.balance_sheet
  else if (statementType === 'cashflow') statement = companyData.value.cashflow
  
  if (!statement) return []
  
  const dataSource = period === 'annual' ? statement.annual : statement.quarterly
  if (!dataSource) return []
  
  return Object.keys(dataSource)
}

const getFinancialValue = (statementType, item, yearOrLtm) => {
  if (!companyData.value) return null
  
  let statement
  if (statementType === 'income') statement = companyData.value.financials
  else if (statementType === 'balance') statement = companyData.value.balance_sheet
  else if (statementType === 'cashflow') statement = companyData.value.cashflow
  
  if (!statement) return null
  
  if (yearOrLtm === 'ltm') {
    return statement.ltm?.[item]
  }
  
  if (!statement.annual || !statement.annual[item]) return null
  
  const itemData = statement.annual[item]
  for (const [key, value] of Object.entries(itemData)) {
    try {
      const date = new Date(key)
      if (date.getFullYear() === yearOrLtm) {
        return value
      }
    } catch {
      continue
    }
  }
  
  return null
}

const getFinancialValueByPeriod = (statementType, item, periodTimestamp, period = 'annual') => {
  if (!companyData.value) return null
  
  let statement
  if (statementType === 'income') statement = companyData.value.financials
  else if (statementType === 'balance') statement = companyData.value.balance_sheet
  else if (statementType === 'cashflow') statement = companyData.value.cashflow
  
  if (!statement) return null
  
  const dataSource = period === 'annual' ? statement.annual : statement.quarterly
  if (!dataSource || !dataSource[item]) return null
  
  const itemData = dataSource[item]
  for (const [key, value] of Object.entries(itemData)) {
    try {
      const date = new Date(key)
      if (date.getTime() === periodTimestamp) {
        return value
      }
    } catch {
      continue
    }
  }
  
  return null
}

const formatPeriodLabel = (timestamp) => {
  try {
    const date = new Date(timestamp)
    if (financialPeriod.value === 'annual') {
      return date.getFullYear().toString()
    } else {
      const year = date.getFullYear()
      const month = date.getMonth()
      const quarter = Math.floor(month / 3) + 1
      return `Q${quarter} ${year}`
    }
  } catch {
    return timestamp
  }
}

const getRevenueGrowthClass = () => {
  const growth = parseFloat(calculateRevenueGrowth())
  if (isNaN(growth)) return ''
  return growth >= 0 ? 'positive' : 'negative'
}

// Analysis generation functions
const saveReport = async (title, content, type) => {
  if (!companyData.value) return
  try {
    await fetch('http://localhost:8000/api/reports/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        content: content,
        report_type: type,
        ticker: companyData.value.ticker
      })
    })
  } catch (e) {
    console.error("Failed to save report", e)
  }
}

const generateAllAnalyses = async () => {
  if (!companyData.value) return
  analyzing.value = true
  
  try {
    analysisProgress.value = 'Generating Company Overview & Industry Analysis...'
    await generateAnalysis()
    
    analysisProgress.value = 'Generating Notes & Disclosures Analysis...'
    await generateNotesAnalysis()
    
    analysisProgress.value = 'Generating Operating Drivers Analysis...'
    await generateDriversAnalysis()
    
    analysisProgress.value = 'Generating Capital Structure Analysis...'
    await generateCapitalAnalysis()
    
    analysisProgress.value = 'Saving complete deep dive report...'
    const combinedReport = `# Deep Dive Analysis: ${companyData.value.company_name} (${companyData.value.ticker})

## Company Overview & Industry Analysis

${analysisReport.value || 'Not generated'}

---

## Notes & Disclosures

${notesReport.value || 'Not generated'}

---

## Operating Drivers

${driversReport.value || 'Not generated'}

---

## Capital Structure & Financing

${capitalReport.value || 'Not generated'}`

    await saveReport(
      `Deep Dive: ${companyData.value.company_name} (${companyData.value.ticker})`,
      combinedReport,
      'deep_dive'
    )
    
    analysisProgress.value = 'Complete!'
  } catch (e) {
    console.error(e)
    alert("Failed to generate complete analysis")
  } finally {
    analyzing.value = false
    setTimeout(() => { analysisProgress.value = '' }, 2000)
  }
}

const generateAnalysis = async () => {
  if (!companyData.value) return
  try {
    const response = await fetch('http://localhost:8000/api/agent/analyze_company', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: companyData.value.ticker,
        company_name: companyData.value.company_name,
        sector: companyData.value.sector
      })
    })
    if (!response.ok) throw new Error('Failed to generate analysis')
    const result = await response.json()
    analysisReport.value = result.report
    await saveReport(`Company Overview: ${companyData.value.company_name}`, result.report, 'company_overview')
  } catch (e) {
    console.error(e)
    throw e
  }
}

const generateNotesAnalysis = async () => {
  if (!companyData.value) return
  analyzingNotes.value = true
  try {
    const response = await fetch('http://localhost:8000/api/agent/analyze_notes_disclosures', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: companyData.value.ticker,
        company_name: companyData.value.company_name,
        sector: companyData.value.sector
      })
    })
    if (!response.ok) throw new Error('Failed to generate analysis')
    const result = await response.json()
    notesReport.value = result.report
    await saveReport(`Notes & Disclosures: ${companyData.value.company_name}`, result.report, 'notes_disclosures')
  } catch (e) {
    console.error(e)
    if (!analyzing.value) alert("Failed to generate notes analysis")
    throw e
  } finally {
    analyzingNotes.value = false
  }
}

const generateDriversAnalysis = async () => {
  if (!companyData.value) return
  analyzingDrivers.value = true
  try {
    const response = await fetch('http://localhost:8000/api/agent/analyze_operating_drivers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: companyData.value.ticker,
        company_name: companyData.value.company_name,
        sector: companyData.value.sector
      })
    })
    if (!response.ok) throw new Error('Failed to generate analysis')
    const result = await response.json()
    driversReport.value = result.report
    await saveReport(`Operating Drivers: ${companyData.value.company_name}`, result.report, 'operating_drivers')
  } catch (e) {
    console.error(e)
    if (!analyzing.value) alert("Failed to generate drivers analysis")
    throw e
  } finally {
    analyzingDrivers.value = false
  }
}

const generateCapitalAnalysis = async () => {
  if (!companyData.value) return
  analyzingCapital.value = true
  try {
    const response = await fetch('http://localhost:8000/api/agent/analyze_capital_structure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: companyData.value.ticker,
        company_name: companyData.value.company_name,
        sector: companyData.value.sector
      })
    })
    if (!response.ok) throw new Error('Failed to generate analysis')
    const result = await response.json()
    capitalReport.value = result.report
    await saveReport(`Capital Structure: ${companyData.value.company_name}`, result.report, 'capital_structure')
  } catch (e) {
    console.error(e)
    if (!analyzing.value) alert("Failed to generate capital analysis")
    throw e
  } finally {
    analyzingCapital.value = false
  }
}

// Chart rendering functions
const renderFinancialCharts = () => {
  if (!companyData.value) return
  
  const charts = [
    { ref: revenueProfitChart, instance: revenueProfitChartInstance },
    { ref: cashflowChart, instance: cashflowChartInstance },
    { ref: assetsChart, instance: assetsChartInstance },
    { ref: liabilitiesChart, instance: liabilitiesChartInstance }
  ]

  charts.forEach(({ ref }) => {
    if (ref.value) {
      const chart = ChartJS.getChart(ref.value)
      if (chart) {
        chart.destroy()
      }
    }
  })
  
  revenueProfitChartInstance = null
  cashflowChartInstance = null
  assetsChartInstance = null
  liabilitiesChartInstance = null
  
  renderRevenueProfitChart()
  renderCashflowChart()
  renderBalanceSheetCharts()
}

const renderRevenueProfitChart = () => {
  if (!revenueProfitChart.value) return
  
  const periods = getFinancialYears('income', financialPeriod.value)
  
  const validData = []
  for (const period of periods) {
    const revenue = getFinancialValueByPeriod('income', 'Total Revenue', period, financialPeriod.value)
    const netIncome = getFinancialValueByPeriod('income', 'Net Income', period, financialPeriod.value)
    
    if (revenue !== null && revenue !== undefined && netIncome !== null && netIncome !== undefined) {
      validData.push({
        period: period,
        label: formatPeriodLabel(period),
        revenue: revenue,
        netIncome: netIncome
      })
    }
  }
  
  validData.reverse()
  
  const labels = validData.map(d => d.label)
  const revenues = validData.map(d => d.revenue)
  const netIncomes = validData.map(d => d.netIncome)
  
  revenueProfitChartInstance = new ChartJS(revenueProfitChart.value, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Revenue',
          data: revenues,
          borderColor: '#42b983',
          backgroundColor: 'rgba(66, 185, 131, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8
        },
        {
          label: 'Net Income',
          data: netIncomes,
          borderColor: '#8e44ad',
          backgroundColor: 'rgba(142, 68, 173, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.dataset.label + ': $' + formatFinancialNumber(context.parsed.y)
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => '$' + formatFinancialNumber(value)
          }
        }
      }
    }
  })
}

const renderCashflowChart = () => {
  if (!cashflowChart.value) return
  
  const periods = getFinancialYears('cashflow', financialPeriod.value)
  
  const validData = []
  for (const period of periods) {
    const operating = getFinancialValueByPeriod('cashflow', 'Operating Cash Flow', period, financialPeriod.value)
    const investing = getFinancialValueByPeriod('cashflow', 'Investing Cash Flow', period, financialPeriod.value)
    const financing = getFinancialValueByPeriod('cashflow', 'Financing Cash Flow', period, financialPeriod.value)
    
    if (operating !== null && operating !== undefined) {
      validData.push({
        period: period,
        label: formatPeriodLabel(period),
        operating: operating || 0,
        investing: investing || 0,
        financing: financing || 0
      })
    }
  }
  
  validData.reverse()
  
  const labels = validData.map(d => d.label)
  const operating = validData.map(d => d.operating)
  const investing = validData.map(d => d.investing)
  const financing = validData.map(d => d.financing)
  
  cashflowChartInstance = new ChartJS(cashflowChart.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Operating CF',
          data: operating,
          backgroundColor: '#42b983'
        },
        {
          label: 'Investing CF',
          data: investing,
          backgroundColor: '#e74c3c'
        },
        {
          label: 'Financing CF',
          data: financing,
          backgroundColor: '#3498db'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.dataset.label + ': $' + formatFinancialNumber(context.parsed.y)
            }
          }
        }
      },
      scales: {
        y: {
          ticks: {
            callback: (value) => '$' + formatFinancialNumber(value)
          }
        }
      }
    }
  })
}

const renderBalanceSheetCharts = () => {
  if (!assetsChart.value || !liabilitiesChart.value) return
  
  const currentAssets = getFinancialValue('balance', 'Current Assets', 'ltm') || 0
  const totalAssets = getFinancialValue('balance', 'Total Assets', 'ltm') || 0
  const nonCurrentAssets = totalAssets - currentAssets
  
  assetsChartInstance = new ChartJS(assetsChart.value, {
    type: 'doughnut',
    data: {
      labels: ['Current Assets', 'Non-Current Assets'],
      datasets: [{
        data: [currentAssets, nonCurrentAssets],
        backgroundColor: ['#42b983', '#95a5a6']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.label + ': $' + formatFinancialNumber(context.parsed)
            }
          }
        }
      }
    }
  })
  
  const currentLiabilities = getFinancialValue('balance', 'Current Liabilities', 'ltm') || 0
  const totalLiabilities = getFinancialValue('balance', 'Total Liabilities Net Minority Interest', 'ltm') || 0
  const equity = getFinancialValue('balance', 'Stockholders Equity', 'ltm') || 0
  const nonCurrentLiabilities = totalLiabilities - currentLiabilities
  
  liabilitiesChartInstance = new ChartJS(liabilitiesChart.value, {
    type: 'doughnut',
    data: {
      labels: ['Current Liabilities', 'Non-Current Liabilities', 'Equity'],
      datasets: [{
        data: [currentLiabilities, nonCurrentLiabilities, equity],
        backgroundColor: ['#e74c3c', '#e67e22', '#3498db']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.label + ': $' + formatFinancialNumber(context.parsed)
            }
          }
        }
      }
    }
  })
}

const prepareOptionsData = () => {
  if (!companyData.value || !companyData.value.trading || !companyData.value.trading.options) return null
  
  const options = companyData.value.trading.options
  if (options.length === 0) return null
  
  const sortedOptions = [...options].sort((a, b) => {
    return new Date(a.expirationDate) - new Date(b.expirationDate)
  })
  
  const labels = sortedOptions.map(opt => {
    const date = new Date(opt.expirationDate)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  })
  
  return {
    labels,
    totalVolumes: sortedOptions.map(opt => opt.totalVolume),
    totalOpenInterests: sortedOptions.map(opt => opt.totalOpenInterest),
    callsVolumes: sortedOptions.map(opt => opt.callsVolume),
    putsVolumes: sortedOptions.map(opt => opt.putsVolume)
  }
}

const renderOptionsVolumeChart = () => {
  if (!optionsVolumeChart.value) return
  
  const chartData = prepareOptionsData()
  if (!chartData) return
  
  const chart = ChartJS.getChart(optionsVolumeChart.value)
  if (chart) {
    chart.destroy()
  }
  
  optionsVolumeChartInstance = new ChartJS(optionsVolumeChart.value, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Total Volume',
          data: chartData.totalVolumes,
          borderColor: '#42b983',
          backgroundColor: 'rgba(66, 185, 131, 0.1)',
          tension: 0.4,
          fill: false
        },
        {
          label: 'Total Open Interest',
          data: chartData.totalOpenInterests,
          borderColor: '#8e44ad',
          backgroundColor: 'rgba(142, 68, 173, 0.1)',
          tension: 0.4,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.dataset.label + ': ' + formatNumberMicro(context.parsed.y)
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => formatNumberMicro(value)
          }
        }
      }
    }
  })
}

const renderOptionsCallsPutsChart = () => {
  if (!optionsCallsPutsChart.value) return
  
  const chartData = prepareOptionsData()
  if (!chartData) return
  
  const chart = ChartJS.getChart(optionsCallsPutsChart.value)
  if (chart) {
    chart.destroy()
  }
  
  optionsCallsPutsChartInstance = new ChartJS(optionsCallsPutsChart.value, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Calls Volume',
          data: chartData.callsVolumes,
          borderColor: '#27ae60',
          backgroundColor: 'rgba(39, 174, 96, 0.1)',
          tension: 0.4,
          fill: false
        },
        {
          label: 'Puts Volume',
          data: chartData.putsVolumes,
          borderColor: '#c0392b',
          backgroundColor: 'rgba(192, 57, 43, 0.1)',
          tension: 0.4,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (context) => {
              return context.dataset.label + ': ' + formatNumberMicro(context.parsed.y)
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => formatNumberMicro(value)
          }
        }
      }
    }
  })
}

// Filings functions
const sortedFilings = computed(() => {
  if (!companyData.value || !companyData.value.filings) return []
  
  const filings = [...companyData.value.filings]
  
  return filings.sort((a, b) => {
    if (filingsSortBy.value === 'type') {
      const comparison = a.type.localeCompare(b.type)
      return filingsSortOrder.value === 'asc' ? comparison : -comparison
    } else if (filingsSortBy.value === 'date') {
      const dateA = new Date(a.date)
      const dateB = new Date(b.date)
      const comparison = dateA - dateB
      return filingsSortOrder.value === 'asc' ? comparison : -comparison
    }
    return 0
  })
})

const sortFilings = (column) => {
  if (filingsSortBy.value === column) {
    filingsSortOrder.value = filingsSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    filingsSortBy.value = column
    filingsSortOrder.value = column === 'date' ? 'desc' : 'asc'
  }
}

const getSortIcon = (column) => {
  if (filingsSortBy.value !== column) return '⇅'
  return filingsSortOrder.value === 'asc' ? '↑' : '↓'
}

const formatFilingDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch {
    return dateStr
  }
}

// Releases functions
const sortedReleases = computed(() => {
  if (!companyData.value || !companyData.value.releases) return []
  
  const releases = [...companyData.value.releases]
  
  return releases.sort((a, b) => {
    if (releasesSortBy.value === 'type') {
      const typeA = a.type || 'Press Release'
      const typeB = b.type || 'Press Release'
      const comparison = typeA.localeCompare(typeB)
      return releasesSortOrder.value === 'asc' ? comparison : -comparison
    } else if (releasesSortBy.value === 'date') {
      const dateA = new Date(a.date)
      const dateB = new Date(b.date)
      const comparison = dateA - dateB
      return releasesSortOrder.value === 'asc' ? comparison : -comparison
    }
    return 0
  })
})

const sortReleases = (column) => {
  if (releasesSortBy.value === column) {
    releasesSortOrder.value = releasesSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    releasesSortBy.value = column
    releasesSortOrder.value = column === 'date' ? 'desc' : 'asc'
  }
}

const getReleaseSortIcon = (column) => {
  if (releasesSortBy.value !== column) return '⇅'
  return releasesSortOrder.value === 'asc' ? '↑' : '↓'
}

// Holders functions
const getInsiderTransactions = () => {
  if (!companyData.value || !companyData.value.holders || !companyData.value.holders.insider) return []
  const insider = companyData.value.holders.insider
  return Object.values(insider).slice(0, 50)
}

const getInstitutionalHolders = () => {
  if (!companyData.value || !companyData.value.holders || !companyData.value.holders.institutional) return []
  const institutional = companyData.value.holders.institutional
  
  const columnNames = Object.keys(institutional)
  if (columnNames.length === 0) return []
  
  const firstColumn = institutional[columnNames[0]]
  if (!firstColumn || typeof firstColumn !== 'object') return []
  
  const rowIndices = Object.keys(firstColumn).map(idx => parseInt(idx)).filter(idx => !isNaN(idx))
  if (rowIndices.length === 0) return []
  
  const holders = rowIndices.map(rowIdx => {
    const row = {}
    columnNames.forEach(col => {
      if (institutional[col] && institutional[col][rowIdx] !== undefined) {
        row[col] = institutional[col][rowIdx]
      }
    })
    return row
  })
  
  holders.sort((a, b) => {
    const dateA = a['Date Reported'] ? new Date(a['Date Reported']) : new Date(0)
    const dateB = b['Date Reported'] ? new Date(b['Date Reported']) : new Date(0)
    if (dateB.getTime() !== dateA.getTime()) {
      return dateB - dateA
    }
    const valueA = a.Value || 0
    const valueB = b.Value || 0
    return valueB - valueA
  })
  
  return holders.slice(0, 50)
}

const formatTradeDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }).toUpperCase()
  } catch {
    return dateStr
  }
}

const extractAction = (text) => {
  if (!text) return 'N/A'
  if (text.toLowerCase().includes('sale')) return 'SELL'
  if (text.toLowerCase().includes('purchase')) return 'PURCHASE'
  if (text.toLowerCase().includes('gift')) return 'STOCK GIFT'
  if (text.toLowerCase().includes('no change')) return 'NO CHANGE'
  if (text.toLowerCase().includes('option')) return 'OPTION EXERCISE'
  return 'OTHER'
}

const getActionClass = (text) => {
  const action = extractAction(text)
  if (action === 'SELL') return 'action-sell'
  if (action === 'PURCHASE') return 'action-purchase'
  return ''
}

const getChangeClass = (pctChange) => {
  if (!pctChange && pctChange !== 0) return ''
  if (pctChange > 0) return 'action-purchase'
  if (pctChange < 0) return 'action-sell'
  return ''
}

const formatPercentChange = (value) => {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return sign + (value * 100).toFixed(2) + '%'
}

// Report Tab Functions
const fetchReports = async () => {
  loadingReports.value = true
  try {
    const response = await fetch('http://localhost:8000/api/reports/')
    if (response.ok) {
      savedReports.value = await response.json()
    }
  } catch (e) {
    console.error("Failed to fetch reports", e)
  } finally {
    loadingReports.value = false
  }
}

const selectReport = async (savedReportSummary) => {
  selectedReportId.value = savedReportSummary.id
  selectedReportTitle.value = savedReportSummary.title || savedReportSummary.ticker
  loadingModal.value = true
  showReportModal.value = true
  
  try {
    const response = await fetch(`http://localhost:8000/api/reports/${savedReportSummary.id}`)
    if (!response.ok) throw new Error('Failed to fetch report content')
    const data = await response.json()
    modalReportContent.value = data.content
  } catch (e) {
    console.error("Failed to load report", e)
    modalReportContent.value = "Failed to load report content."
  } finally {
    loadingModal.value = false
  }
}

const closeReportModal = () => {
  showReportModal.value = false
  selectedReportId.value = null
  selectedReportTitle.value = ''
  modalReportContent.value = ''
}

const formattedReport = computed(() => {
  try {
    return marked(report.value)
  } catch {
    return report.value.replace(/\n/g, '<br>')
  }
})

const formattedModalReport = computed(() => {
  try {
    return marked(modalReportContent.value)
  } catch {
    return modalReportContent.value.replace(/\n/g, '<br>')
  }
})

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  loadingReport.value = true
  reportError.value = null
  report.value = ''
  
  try {
    reportStatusMessage.value = 'Uploading and extracting text...'
    const formData = new FormData()
    formData.append('file', file)
    
    const uploadResponse = await fetch('http://localhost:8000/api/external/upload', {
      method: 'POST',
      body: formData
    })
    
    if (!uploadResponse.ok) throw new Error('Upload failed')
    const uploadData = await uploadResponse.json()
    
    reportStatusMessage.value = 'Generating AI Report...'
    const agentResponse = await fetch('http://localhost:8000/api/agent/generate_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data_context: uploadData.content_preview,
        prompt_customization: "Analyze this financial document and provide a summary."
      })
    })
    
    if (!agentResponse.ok) throw new Error('Report generation failed')
    const agentData = await agentResponse.json()
    report.value = agentData.report

  } catch (err) {
    reportError.value = err.message
  } finally {
    loadingReport.value = false
  }
}

onMounted(() => {
  // Load stock data for default ticker
  loadStockData()
  // Initial check for forecast events
  checkForecastEvents()
  // Set up periodic check (every minute)
  forecastCheckInterval = setInterval(() => {
    checkForecastEvents()
  }, 60000) // Check every minute
  
  // Load company data for default stock
  if (selectedStock.value) {
    fetchCompanyData()
  }
  
  // Fetch saved reports
  fetchReports()
})

// Watch selectedTimePeriod to reload data when period changes
watch(selectedTimePeriod, () => {
  if (selectedStock.value) {
    loadStockData()
  }
})

// Cleanup interval on unmount
onUnmounted(() => {
  if (forecastCheckInterval) {
    clearInterval(forecastCheckInterval)
  }
})
</script>

<style scoped>
.timeline-view {
  padding: 20px 20px 20px 0;
  max-width: 1800px;
  margin: 0 auto;
  background: #ffffff;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 2em;
  font-weight: 600;
}

.subtitle {
  color: #666666;
  margin: 0;
  font-size: 0.95em;
}

.price-info {
  text-align: right;
}

.current-price {
  font-size: 2em;
  font-weight: bold;
  color: #000000;
  margin-bottom: 5px;
}

.price-change {
  font-size: 1em;
  font-weight: 500;
}

.price-change.positive {
  color: #42b983;
}

.price-change.negative {
  color: #e74c3c;
}

.stock-selector {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.stock-selector label {
  color: #000000;
  font-weight: 500;
}

.stock-selector input {
  flex: 1;
  min-width: 200px;
  padding: 10px 15px;
  background: #ffffff;
  color: #000000;
  border: 1px solid #cccccc;
  border-radius: 6px;
  font-size: 1em;
}

.stock-selector input:focus {
  outline: none;
  border-color: #3498db;
}

.stock-selector input::placeholder {
  color: #999999;
}

.stock-selector button {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: all 0.2s;
}

.stock-selector button:hover:not(:disabled) {
  background: #2980b9;
}

.stock-selector button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-indicator {
  color: #3498db;
  font-size: 0.9em;
  margin-left: 10px;
}

.stock-error {
  color: #e74c3c;
  font-size: 0.9em;
  margin-left: 10px;
  padding: 5px 10px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
}

.stock-selector select {
  background: #2c3e50;
  color: #fff;
  border: 1px solid #34495e;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 1em;
  cursor: pointer;
}

.stock-selector select:hover {
  border-color: #42b983;
}

.chart-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.chart-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.timeframe-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.timeframe-selector button {
  padding: 6px 14px;
  border: 1px solid #cccccc;
  background: #ffffff;
  color: #000000;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: all 0.2s;
}

.timeframe-selector button:hover {
  border-color: #3498db;
  background: #f0f8ff;
}

.timeframe-selector button.active {
  border-color: #3498db;
  background: #3498db;
  color: #fff;
}

.chart-container {
  height: 400px;
  position: relative;
}

.events-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.tab-selector {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: transparent;
  color: #666666;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  position: relative;
  top: 2px;
}

.tab-btn:hover {
  color: #000000;
  background: #f8f9fa;
}

.tab-btn.active {
  color: #000000;
  border-bottom-color: #3498db;
  font-weight: 600;
}

.tab-content {
  min-height: 200px;
}

.company-basic-content,
.report-content {
  padding: 20px 0;
}

.company-basic-content h3,
.report-content h3 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.company-basic-content p,
.report-content p {
  color: #666666;
  margin: 0;
}

/* Report Tab Specific Styles */
.report-tab-content {
  padding: 0;
}

.report-container {
  display: flex;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

.main-report-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}

.reports-sidebar {
  width: 250px;
  background: #f8f9fa;
  border-left: 1px solid #cccccc;
  padding: 15px;
  overflow-y: auto;
  border-radius: 8px;
}

.reports-sidebar h3 {
  color: #000000;
  font-weight: 600;
  margin: 0 0 15px 0;
  font-size: 1.1em;
}

.report-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.report-list li {
  padding: 10px;
  border-bottom: 1px solid #e0e0e0;
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 6px;
  margin-bottom: 5px;
  background: #ffffff;
}

.report-list li:hover {
  background: #e9ecef;
}

.report-list li.active {
  background: #e3f2fd;
  border-left: 4px solid #3498db;
}

.report-ticker {
  font-weight: 600;
  color: #000000;
  display: block;
}

.upload-section {
  margin-bottom: 20px;
  padding: 40px;
  border: 2px dashed #cccccc;
  border-radius: 8px;
  text-align: center;
  background: #fafafa;
}

.upload-section h3 {
  color: #000000;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.upload-section input[type="file"] {
  padding: 10px;
  border: 1px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  cursor: pointer;
}

.loading-small {
  text-align: center;
  margin: 20px 0;
  color: #666666;
  font-size: 0.9em;
}

.report-body {
  line-height: 1.6;
  color: #000000;
}

.report-body :deep(h1), .report-body :deep(h2), .report-body :deep(h3) {
  color: #000000;
  margin-top: 1.5em;
  font-weight: 600;
}

.report-body :deep(ul), .report-body :deep(ol) {
  padding-left: 20px;
}

.report-body :deep(p) {
  margin-bottom: 1em;
  color: #000000;
}

.no-reports {
  color: #666666;
  font-style: italic;
  text-align: center;
  margin-top: 20px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}

.modal-header h3 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.modal-body {
  overflow-y: auto;
  flex: 1;
}

.close-btn {
  padding: 6px 12px;
  background: #95a5a6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.close-btn:hover {
  background: #7f8c8d;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.search-bar input:focus {
  outline: none;
  border-color: #3498db;
}

.search-bar button {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: all 0.2s;
}

.search-bar button:hover:not(:disabled) {
  background: #2980b9;
}

.search-bar button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666666;
}

.error {
  padding: 15px;
  background: #fee;
  color: #c33;
  border-radius: 6px;
  margin-bottom: 20px;
}

.company-info {
  margin-top: 20px;
}

.company-header {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.company-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.5em;
  font-weight: 600;
}

.company-price-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.company-price {
  font-size: 1.8em;
  font-weight: bold;
  color: #000000;
}

.company-sector {
  color: #666666;
  font-size: 1em;
}

.company-section {
  margin-bottom: 30px;
}

.company-section h4 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.company-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-label {
  color: #666666;
  font-weight: 500;
}

.detail-value {
  color: #000000;
  font-weight: 600;
}

.ratios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.ratio-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  text-align: center;
}

.ratio-label {
  color: #666666;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.ratio-value {
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.financial-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.financial-metric {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
}

.metric-label {
  color: #666666;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.metric-value {
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.no-company-data {
  text-align: center;
  padding: 40px;
  color: #666666;
}

.event-filters {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-label {
  color: #000000;
  font-weight: 500;
  font-size: 0.95em;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 2px solid #cccccc;
  background: #ffffff;
  color: #000000;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #3498db;
  background: #f0f8ff;
}

.filter-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.filter-btn.clear-all {
  border-color: #cccccc;
  color: #666666;
}

.filter-btn.clear-all:hover {
  border-color: #999999;
  background: #f8f9fa;
}

.filter-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.filter-dot.positive {
  background-color: #42b983;
}

.filter-dot.negative {
  background-color: #e74c3c;
}

.filter-dot.neutral {
  background-color: #95a5a6;
}

.category-btn {
  border-color: #7f8c8d;
}

.category-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.event-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.event-category-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.event-category-badge.macro {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.event-category-badge.micro {
  background-color: #fff3e0;
  color: #e65100;
}

.event-category-badge.market {
  background-color: #e3f2fd;
  color: #1565c0;
}

.event-category-badge.industry {
  background-color: #f3e5f5;
  color: #6a1b9a;
}

.event-category-badge.product {
  background-color: #fce4ec;
  color: #c2185b;
}

.event-item.forecast {
  border-left: 3px dashed #7f8c8d;
}

.event-content.forecast {
  opacity: 0.9;
}

.event-dot.forecast {
  border: 2px dashed #fff;
  box-sizing: border-box;
}

.forecast-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background-color: #fff3cd;
  color: #856404;
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: 600;
  text-transform: uppercase;
}

.status-btn {
  border-color: #7f8c8d;
}

.status-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #000000;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-hint {
  margin: 5px 0 0 0;
  font-size: 0.85em;
  color: #666666;
  font-style: italic;
}

.legend {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #000000;
  font-size: 0.9em;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.legend-dot.positive {
  background-color: #42b983;
}

.legend-dot.negative {
  background-color: #e74c3c;
}

.legend-dot.neutral {
  background-color: #95a5a6;
}

.events-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.5em;
  font-weight: 600;
  flex: 1;
}

.add-event-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
}

.add-event-btn:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s;
  cursor: pointer;
}

.event-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.event-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.event-dot.positive {
  background-color: #42b983;
}

.event-dot.negative {
  background-color: #e74c3c;
}

.event-dot.neutral {
  background-color: #95a5a6;
}

.event-content {
  flex: 1;
}

.event-title {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
}

.event-date {
  margin: 0 0 8px 0;
  color: #666666;
  font-size: 0.9em;
}

.event-description {
  margin: 0;
  color: #333333;
  font-size: 0.95em;
  line-height: 1.5;
}

.no-events {
  text-align: center;
  padding: 40px;
  color: #666666;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2em;
  color: #666666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #000000;
}

.event-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #000000;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #3498db;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 30px;
}

.cancel-btn,
.submit-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
}

.cancel-btn:hover {
  background: #7f8c8d;
}

.submit-btn {
  background: #42b983;
  color: white;
}

.submit-btn:hover {
  background: #35a372;
}

/* Micro Economics Styles */
.company-data {
  margin-top: 20px;
}

.micro-tabs {
  display: flex;
  gap: 5px;
  margin-bottom: 20px;
  border-bottom: 2px solid #cccccc;
  flex-wrap: nowrap;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
}

.micro-tabs::-webkit-scrollbar {
  display: none;
}

.micro-tabs button {
  padding: 10px 15px;
  border: none;
  background: #f8f9fa;
  color: #000000;
  cursor: pointer;
  font-size: 0.9em;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.micro-tabs button:hover {
  background: #e9ecef;
}

.micro-tabs button.active {
  background: #ffffff;
  color: #000000;
  font-weight: 600;
  border-bottom-color: #3498db;
}

.micro-tab-content {
  padding: 10px 0;
}

.micro-tab-pane {
  padding: 10px 0;
}

.ai-section {
  margin-bottom: 30px;
}

.ai-btn {
  background: #8e44ad;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 1.1em;
  cursor: pointer;
  margin-bottom: 20px;
}

.ai-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.progress-indicator {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-weight: bold;
  color: #2e7d32;
}

.analysis-section {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 2px solid #eee;
}

.analysis-section h4 {
  color: #000000;
  margin-bottom: 15px;
  font-weight: 600;
}

.report-content {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  line-height: 1.6;
  margin-bottom: 20px;
}

.info-message {
  background: #fff3cd;
  padding: 15px;
  border-radius: 4px;
  color: #856404;
  margin-top: 10px;
}

.metrics-viz,
.capital-viz {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.metric-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #42b983;
  position: relative;
}

.metric-card.highlight {
  border-left-color: #8e44ad;
  background: #f3e5f5;
}

.metric-label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.5em;
  font-weight: bold;
  color: #000000;
}

.metric-trend {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 1.5em;
}

.metric-trend.positive {
  color: #42b983;
}

.metric-trend.negative {
  color: #e74c3c;
}

.financials-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.financials-header h4 {
  margin: 0;
}

.period-selector {
  display: flex;
  gap: 0;
  border: 2px solid #42b983;
  border-radius: 6px;
  overflow: hidden;
}

.period-selector button {
  padding: 8px 20px;
  border: none;
  background: white;
  color: #42b983;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.period-selector button:hover {
  background: #e8f5e9;
}

.period-selector button.active {
  background: #42b983;
  color: white;
}

.financial-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.summary-label {
  font-size: 0.85em;
  opacity: 0.9;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-change {
  font-size: 0.9em;
  font-weight: 600;
}

.summary-change.positive {
  color: #a8e6cf;
}

.summary-change.negative {
  color: #ffaaa5;
}

.charts-row {
  display: flex;
  gap: 20px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.chart-section {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
  min-width: 300px;
}

.chart-section h5 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
}

.chart-container {
  height: 300px;
  position: relative;
}

.balance-composition {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.composition-chart {
  flex: 1;
  min-width: 200px;
  text-align: center;
}

.composition-chart h6 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.composition-chart canvas {
  max-height: 250px;
}

.detailed-tables {
  margin-top: 40px;
}

.detailed-tables details {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 15px;
  padding: 15px;
}

.detailed-tables summary {
  cursor: pointer;
  font-size: 1.1em;
  padding: 10px;
  user-select: none;
  color: #2c3e50;
}

.detailed-tables summary:hover {
  background: #f8f9fa;
  border-radius: 4px;
}

.detailed-tables details[open] summary {
  margin-bottom: 20px;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.detailed-tables .table-container {
  overflow-x: auto;
}

.detailed-tables table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 0.85em;
}

.detailed-tables th,
.detailed-tables td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: right;
  white-space: nowrap;
  color: #2c3e50;
}

.detailed-tables th:first-child,
.detailed-tables td:first-child {
  text-align: left;
  font-weight: bold;
  position: sticky;
  left: 0;
  background: white;
  z-index: 2;
  min-width: 200px;
  max-width: 300px;
}

.detailed-tables .item-name {
  font-size: 0.9em;
  color: #2c3e50;
}

.detailed-tables th {
  background: #f2f2f2;
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: bold;
}

.detailed-tables .ltm-header {
  background: #d4edda !important;
  color: #155724;
  font-weight: bold;
}

.detailed-tables .ltm-col {
  background: #e8f5e9;
  font-weight: bold;
  color: #2e7d32;
}

.ratios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.ratio-card {
  background: #fff;
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 8px;
  color: #2c3e50;
}

.ratio-card h5 {
  margin-top: 0;
  color: #42b983;
}

.ratio-card p {
  margin: 8px 0;
}

.filings-container {
  margin-top: 20px;
}

.filings-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.filings-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.filings-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  font-size: 0.95em;
  color: white;
}

.filings-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.filings-table th.sortable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.filings-table .sort-icon {
  margin-left: 8px;
  font-size: 0.9em;
  opacity: 0.8;
}

.filings-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.filings-table tbody tr:hover {
  background: #f8f9fa;
}

.filings-table tbody tr:last-child {
  border-bottom: none;
}

.filings-table td {
  padding: 12px 15px;
  font-size: 0.9em;
  color: #000;
}

.filing-type {
  font-weight: 600;
  color: #000;
}

.filing-date {
  color: #000;
}

.filing-title {
  color: #000;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-link {
  color: #999;
  font-style: italic;
}

.filing-link a {
  color: #42b983;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.filing-link a:hover {
  color: #35a372;
  text-decoration: underline;
}

.trade-log-tabs {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.trade-log-tabs button {
  padding: 8px 20px;
  background: #2c3e50;
  color: white;
  border: 1px solid #34495e;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.trade-log-tabs button:hover {
  background: #34495e;
}

.trade-log-tabs button.active {
  background: #3498db;
  border-color: #3498db;
}

.trade-log-container {
  margin-top: 20px;
}

.section-heading {
  color: #000000;
  margin: 30px 0 15px 0;
  font-size: 1.2em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 8px;
}

.trade-log-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  color: #000000;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #cccccc;
}

.trade-log-table thead {
  background: #f8f9fa;
}

.trade-log-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  font-size: 0.85em;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: #f8f9fa;
  border-bottom: 2px solid #cccccc;
}

.trade-log-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.trade-log-table tbody tr:hover {
  background: #f8f9fa;
}

.trade-log-table tbody tr:last-child {
  border-bottom: none;
}

.trade-log-table td {
  padding: 12px 15px;
  font-size: 0.9em;
  background: #ffffff;
  color: #000000;
}

.trade-log-table tbody tr:hover td {
  background: #f8f9fa;
}

.trade-date {
  color: #666666;
  font-size: 0.85em;
}

.trade-action {
  font-weight: 600;
  text-transform: uppercase;
}

.trade-action.action-purchase {
  color: #3498db;
}

.trade-action.action-sell {
  color: #e74c3c;
}

.trade-shares,
.trade-value,
.trade-holdings {
  text-align: right;
  font-family: 'Courier New', monospace;
}

.trade-party {
  color: #666666;
  font-size: 0.85em;
}

.trade-insider {
  color: #000000;
  font-weight: 500;
}

.options-charts-container {
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.options-chart-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.options-chart-section h5 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #000000;
  font-weight: 600;
}

.options-chart-section .chart-container {
  height: 400px;
  position: relative;
}

.no-company-data {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

</style>
