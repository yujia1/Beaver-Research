<template>
  <div class="timeline-view">
    <div class="page-header">
      <div>
        <h1>Stock Price Timeline</h1>
        <p class="subtitle">Track stock price movements and key events over time</p>
      </div>
      <div class="price-info" v-if="selectedStock">
        <div class="current-price-wrapper">
          <span v-if="todayChangePercent !== 0" class="today-change" :class="todayChangePercent >= 0 ? 'positive' : 'negative'">
            {{ todayChangePercent >= 0 ? '+' : '' }}{{ todayChangePercent.toFixed(2) }}%
          </span>
          <span class="current-price">${{ currentPrice.toFixed(2) }}</span>
        </div>
        <div class="price-change" :class="priceChange >= 0 ? 'positive' : 'negative'">
          {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }} ({{ priceChangePercent >= 0 ? '+' : '' }}{{ priceChangePercent.toFixed(2) }}%) since {{ referenceDate }}
        </div>
      </div>
      <div v-else class="price-info">
        <div class="current-price" style="color: #999999;">No Stock Selected</div>
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
        <h2>{{ selectedStock || 'No Stock Selected' }} - {{ timelineYear }} Price Timeline</h2>
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
        <Line :key="`chart-${events.length}-${selectedCreatorId}-${categoryFilters.macro}-${categoryFilters.micro}-${categoryFilters.market}-${categoryFilters.industry}-${categoryFilters.product}-${selectedTimePeriod}`" :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Key Events Section Removed -->
    <div class="events-card">
      <div class="events-header">
        <h2>Company Data</h2>
      </div>

      <!-- Tab Selector -->
      <div class="tab-selector">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'company' }"
          @click="activeTab = 'company'"
        >
          Company Basic
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'productivity' }"
          @click="activeTab = 'productivity'"
        >
          PolyMarket
        </button>
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
              <button :class="{ active: microTab === 'filings' }" @click="microTab = 'filings'">Filings</button>
              <button :class="{ active: microTab === 'release' }" @click="microTab = 'release'">Release</button>
              <button :class="{ active: microTab === 'holders' }" @click="microTab = 'holders'">Holders</button>
              <button :class="{ active: microTab === 'trading' }" @click="microTab = 'trading'">Trading</button>
            </div>

            <!-- Micro Tab Content -->
            <div class="micro-tab-content">
              <!-- Overview Tab -->
              <div v-if="microTab === 'overview'" class="micro-tab-pane">
                <div class="overview-layout">
                  <!-- Left Side: Latest 10K -->
                  <div class="tenk-section">
                    <div class="section-header">
                      <h4>Latest 10K</h4>
                      <button @click="fetch10KChunks" :disabled="loading10K" class="refresh-btn">
                        {{ loading10K ? 'Loading...' : 'Refresh' }}
                      </button>
                    </div>
                    
                    <div v-if="loading10K" class="loading">Loading 10-K filing...</div>
                    <div v-else-if="tenKError" class="error">{{ tenKError }}</div>
                    <div v-else-if="tenKChunks" class="tenk-content">
                      <div class="tenk-full-html" v-html="tenKChunks"></div>
                    </div>
                    <div v-else class="no-data">No 10-K data available. Click Refresh to load.</div>
                  </div>
                  
                  <!-- Right Side: Company Overview & Industry Analysis -->
                  <div class="analysis-section-wrapper">
                    <div class="analysis-report-section">
                      <div class="section-header">
                        <h4>Company Overview & Deep Dive Analysis</h4>
                        <button @click="generateAllAnalyses" :disabled="analyzing || !hasPaid" class="refresh-btn" :class="{ 'disabled': !hasPaid }">
                          {{ analyzing ? 'Generating...' : (!hasPaid ? '🔒 Payment Required - Generate' : 'Generate') }}
                        </button>
                      </div>
                      
                      <p v-if="!hasPaid && !checkingPayment" class="payment-notice">
                        Payment required to generate analysis. <a href="/research" style="color: #3498db; text-decoration: underline;">Visit Research page to complete payment</a>
                      </p>
                      
                      <div v-if="analyzing" class="progress-indicator">
                        <p>{{ analysisProgress }}</p>
                      </div>
                      
                      <div v-if="analysisReport" class="analysis-report-content">
                        <div class="analysis-html-content" v-html="renderMarkdown(analysisReport)"></div>
                      </div>
                      <div v-else class="no-data">
                        <p>No analysis available. Click "Generate" to create a Company Overview & Deep dive Analysis.</p>
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
                          <template v-for="(items, category) in categorizeFinancialItems('income', financialPeriod)" :key="category">
                            <tr class="category-header" @click="toggleCategory('income', category)">
                              <td class="category-name">
                                <span class="expand-icon">{{ isCategoryExpanded('income', category) ? '▼' : '▶' }}</span>
                                {{ category }}
                              </td>
                              <td class="ltm-col">-</td>
                              <td v-for="period in getFinancialYears('income', financialPeriod)" :key="period">-</td>
                            </tr>
                            <template v-if="isCategoryExpanded('income', category)">
                              <tr v-for="item in items" :key="item" class="category-item">
                                <td class="item-name">{{ item }}</td>
                                <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('income', item, 'ltm')) }}</td>
                                <td v-for="period in getFinancialYears('income', financialPeriod)" :key="period">
                                  {{ formatFinancialNumber(getFinancialValueByPeriod('income', item, period, financialPeriod)) }}
                                </td>
                              </tr>
                            </template>
                          </template>
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
                          <template v-for="(items, category) in categorizeFinancialItems('balance', financialPeriod)" :key="category">
                            <tr class="category-header" @click="toggleCategory('balance', category)">
                              <td class="category-name">
                                <span class="expand-icon">{{ isCategoryExpanded('balance', category) ? '▼' : '▶' }}</span>
                                {{ category }}
                              </td>
                              <td class="ltm-col">-</td>
                              <td v-for="period in getFinancialYears('balance', financialPeriod)" :key="period">-</td>
                            </tr>
                            <template v-if="isCategoryExpanded('balance', category)">
                              <tr v-for="item in items" :key="item" class="category-item">
                                <td class="item-name">{{ item }}</td>
                                <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('balance', item, 'ltm')) }}</td>
                                <td v-for="period in getFinancialYears('balance', financialPeriod)" :key="period">
                                  {{ formatFinancialNumber(getFinancialValueByPeriod('balance', item, period, financialPeriod)) }}
                                </td>
                              </tr>
                            </template>
                          </template>
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
                          <template v-for="(items, category) in categorizeFinancialItems('cashflow', financialPeriod)" :key="category">
                            <tr class="category-header" @click="toggleCategory('cashflow', category)">
                              <td class="category-name">
                                <span class="expand-icon">{{ isCategoryExpanded('cashflow', category) ? '▼' : '▶' }}</span>
                                {{ category }}
                              </td>
                              <td class="ltm-col">-</td>
                              <td v-for="period in getFinancialYears('cashflow', financialPeriod)" :key="period">-</td>
                            </tr>
                            <template v-if="isCategoryExpanded('cashflow', category)">
                              <tr v-for="item in items" :key="item" class="category-item">
                                <td class="item-name">{{ item }}</td>
                                <td class="ltm-col">{{ formatFinancialNumber(getFinancialValue('cashflow', item, 'ltm')) }}</td>
                                <td v-for="period in getFinancialYears('cashflow', financialPeriod)" :key="period">
                                  {{ formatFinancialNumber(getFinancialValueByPeriod('cashflow', item, period, financialPeriod)) }}
                                </td>
                              </tr>
                            </template>
                          </template>
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
                <div v-else class="no-data">release data will be available soon</div>
              </div>

              <!-- Holders Tab -->
              <div v-if="microTab === 'holders'" class="micro-tab-pane">
                <h4>Trade Log</h4>
                
                <div class="trade-log-tabs">
                  <button :class="{ active: holdersView === 'all' }" @click="holdersView = 'all'">All</button>
                  <button :class="{ active: holdersView === 'institutions' }" @click="handleInstitutionsClick">Institutions</button>
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
                  <div v-if="loadingInstitutionalHolders" class="loading">Loading institutional holders...</div>
                  <table v-else-if="getInstitutionalHolders().length > 0" class="trade-log-table">
                    <thead>
                      <tr>
                        <th>DATE REPORTED</th>
                        <th>HOLDER</th>
                        <th>SHARES</th>
                        <th>VALUE</th>
                        <th>% HELD</th>
                        <th>ACTION</th>
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
                        <td class="trade-action" :class="getActionClass(holder.action || holder.pctChange)">
                          {{ holder.action || (holder.pctChange > 0 ? 'BUY' : holder.pctChange < 0 ? 'SELL' : 'HOLD') }}
                        </td>
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
                    <p>Put/Call Ratio: {{ getPutCallRatio() }}</p>
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

      <!-- PolyMarket Tab Content -->
      <div v-if="activeTab === 'productivity'" class="tab-content productivity-tab-content">
        <div v-if="!selectedStock" class="empty-deck">
          <p>Please select a stock ticker to view PolyMarket data.</p>
        </div>
        <div v-else class="content-section">
          <div v-if="loadingPolyMarket" class="loading-state">
            <p>Loading PolyMarket data...</p>
          </div>
          <div v-else-if="polyMarketError" class="error-message">
            <p>{{ polyMarketError }}</p>
          </div>
          <div v-else-if="polyMarketData" class="polymarket-content">
            <div v-if="polyMarketData.is_real_data === false" class="polymarket-warning">
              <strong>Note:</strong> No PolyMarket data available for {{ selectedStock }}. Displaying estimated fallback data based on current stock price. These odds are based on monte carlo simulation&normal distribution for trading decisions.
            </div>
            <div class="polymarket-header">
              <h3>📊 PolyMarket - {{ selectedStock }}</h3>
              <p class="polymarket-question">{{ polyMarketData.question }}</p>
            </div>
            <div class="polymarket-chart-container">
              <canvas ref="polyMarketChart"></canvas>
            </div>
            <div class="polymarket-table">
              <table>
                <thead>
                  <tr>
                    <th>Price Target</th>
                    <th>Odds</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="target in polyMarketData.targets" :key="target.target">
                    <td>{{ target.target }}</td>
                    <td class="odds-value">{{ target.odds }}%</td>
                  </tr>
                </tbody>
              </table>
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
  BarController,
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
  BarController,
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
const selectedStock = ref('')
const stockSearchInput = ref('')
const timelineYear = ref('2024')
const referenceDate = ref('')
const currentPrice = ref(0)
const priceChange = ref(0)
const priceChangePercent = ref(0)
const todayChangePercent = ref(0) // Today's percentage change
const loadingStock = ref(false)
const stockError = ref(null)

// Time period selector
const selectedTimePeriod = ref('daily')
const timePeriods = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Yearly', value: 'yearly' },
  { label: 'Max', value: 'max' }
]

// User info and role check
const user = ref(null)
const isCreator = computed(() => {
  if (!user.value) {
    console.log('isCreator: user.value is null')
    return false
  }
  const role = user.value.role
  const isCreatorRole = role === 'creator' || role === 'admin'
  console.log('isCreator check:', { username: user.value.username, role, isCreatorRole })
  return isCreatorRole
})

// Creator selector
const creators = ref([])
const selectedCreatorId = ref(null)
const loadingCreators = ref(false)

// Events - now loaded from API
const events = ref([])
const loadingEvents = ref(false)

// Filtered events based on selected creator (for chart display)
const filteredEventsForChart = computed(() => {
  // Always filter by selected creator's user_id
  if (selectedCreatorId.value === null) {
    return [] // No creator selected, show no events
  }
  return events.value.filter(event => event.user_id === selectedCreatorId.value)
})

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

// Financial statement expanded categories state
const expandedCategories = ref({
  income: new Set(),
  balance: new Set(),
  cashflow: new Set()
})
const financialPeriod = ref('annual')

// Analysis state
const analyzing = ref(false)
const analysisReport = ref(null)
const analysisProgress = ref('')
const hasPaid = ref(false)
const checkingPayment = ref(true)

// 10-K chunks state
const tenKChunks = ref(null)
const loading10K = ref(false)
const tenKError = ref(null)


// Computed properties
const currentCard = computed({
  get: () => {
    if (linkedCards.value.length === 0) {
      return { id: null, content: '', sentenceId: null }
    }
    const card = linkedCards.value.find(c => c.id === selectedSentenceId.value)
    return card || { id: null, content: '', sentenceId: null }
  },
  set: (value) => {
    if (selectedSentenceId.value) {
      const card = linkedCards.value.find(c => c.id === selectedSentenceId.value)
      if (card) {
        card.content = value.content
        saveReportData()
      }
    }
  }
})

// Chart refs for Micro Economics
const revenueProfitChart = ref(null)
const cashflowChart = ref(null)
const assetsChart = ref(null)
const liabilitiesChart = ref(null)
const optionsVolumeChart = ref(null)
const optionsCallsPutsChart = ref(null)
const polyMarketChart = ref(null)

// Chart instances
let revenueProfitChartInstance = null
let cashflowChartInstance = null
let assetsChartInstance = null
let liabilitiesChartInstance = null
let optionsVolumeChartInstance = null
let optionsCallsPutsChartInstance = null
let polyMarketChartInstance = null

// PolyMarket data
const polyMarketData = ref(null)
const loadingPolyMarket = ref(false)
const polyMarketError = ref(null)

// Filings sorting
const filingsSortBy = ref('date')
const filingsSortOrder = ref('desc')

// Releases sorting
const releasesSortBy = ref('date')
const releasesSortOrder = ref('desc')

// Holders view
const holdersView = ref('all')



// Category filters
const categoryFilters = ref({
  macro: true,
  micro: true,
  market: true,
  industry: true,
  product: true
})



// Events state removed

const stockData = ref([]) // Populated with real data from API

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
      // Show date for monthly view - show every data point with month and year
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      const year = date.getFullYear()
      return `${month} ${day}, ${year}`
    } else if (selectedTimePeriod.value === 'yearly') {
      // Show date for yearly view - show every data point with full date
      const month = date.toLocaleString('default', { month: 'short' })
      const day = date.getDate()
      const year = date.getFullYear()
      return `${month} ${day}, ${year}`
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
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
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
    
    // Get today's percentage change from API response
    todayChangePercent.value = data.today_change_percent || 0
    
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
  
  try {
    const response = await fetch(`http://localhost:8000/api/internal/micro/${selectedStock.value.toUpperCase()}`)
    if (!response.ok) throw new Error('Failed to fetch company data')
    companyData.value = await response.json()
    
    // Fetch 10-K chunks when company data is loaded
    if (microTab.value === 'overview') {
      fetch10KChunks()
    }
    
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

const fetch10KChunks = async () => {
  if (!selectedStock.value) return
  loading10K.value = true
  tenKError.value = null
  
  try {
    const response = await fetch(`http://localhost:8000/api/agent/10k/${selectedStock.value.toUpperCase()}`)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch 10-K' }))
      throw new Error(errorData.detail || 'Failed to fetch 10-K')
    }
    const data = await response.json()
    tenKChunks.value = data.content
  } catch (err) {
    tenKError.value = err.message || 'Error loading 10-K filing'
    console.error('Error fetching 10-K:', err)
  } finally {
    loading10K.value = false
  }
}

// Watch selectedStock to auto-fetch company data
watch(selectedStock, (newStock, oldStock) => {
  // Fetch institutional holders when stock changes
  if (newStock && activeTab.value === 'company' && microTab.value === 'holders') {
    fetchInstitutionalHolders()
  }
  // Clear price info when stock is cleared
  if (!newStock) {
    currentPrice.value = 0
    priceChange.value = 0
    priceChangePercent.value = 0
    todayChangePercent.value = 0
    referenceDate.value = ''
    stockData.value = []

    companyData.value = null
    return
  }
  
  // Fetch events for the new ticker
// Events logic removed
  
  // Always fetch company data if on company tab when stock changes
  // This ensures Key Logs (Company Basic) always uses the same ticker as Stock Price Timeline
  if (activeTab.value === 'company' && selectedStock.value) {
    fetchCompanyData()
  }
  
  
  // Fetch PolyMarket data if on PolyMarket tab
  if (selectedStock.value && activeTab.value === 'productivity') {
    fetchPolyMarketData()
  }
  
  // Reload stock data for the new ticker
  if (selectedStock.value) {
    loadStockData()
  }
})

// Watch activeTab to fetch company data when switching to company tab
watch(activeTab, (newTab) => {
  // Always fetch company data when switching to company tab if we have a selected stock
  // This ensures the data matches the current selectedStock
  if (newTab === 'company' && selectedStock.value) {
    // Check if we need to fetch (no data or data is for different ticker)
    if (!companyData.value || companyData.value.ticker !== selectedStock.value.toUpperCase()) {
      fetchCompanyData()
    }
  }
  
  
  // Fetch PolyMarket data when switching to PolyMarket tab
  if (newTab === 'productivity' && selectedStock.value) {
    fetchPolyMarketData()
  }
})

// Watch microTab and holdersView to fetch data when switching tabs
watch([microTab, holdersView], async () => {
  console.log(`Watcher triggered: microTab=${microTab.value}, holdersView=${holdersView.value}, selectedStock=${selectedStock.value}`)
  // Fetch institutional holders when switching to holders tab
  if (microTab.value === 'holders' && holdersView.value === 'institutions' && selectedStock.value) {
    console.log('Calling fetchInstitutionalHolders from watcher')
    fetchInstitutionalHolders()
  }
}, { immediate: true })

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
  if (companyData.value && microTab.value === 'overview' && !tenKChunks.value) {
    fetch10KChunks()
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

// Categorize financial items into groups
const categorizeFinancialItems = (statementType, period = 'annual') => {
  const allItems = getFinancialItems(statementType, period)
  const categories = {}
  
  if (statementType === 'income') {
    // Income Statement categories
    const revenueItems = allItems.filter(item => 
      item.toLowerCase().includes('revenue') || 
      item.toLowerCase().includes('sales') ||
      item === 'Total Revenue'
    )
    const costItems = allItems.filter(item => 
      item.toLowerCase().includes('cost') && 
      !item.toLowerCase().includes('operating')
    )
    const operatingExpenseItems = allItems.filter(item => 
      item.toLowerCase().includes('operating') ||
      item.toLowerCase().includes('sga') ||
      item.toLowerCase().includes('r&d') ||
      item.toLowerCase().includes('research')
    )
    const otherItems = allItems.filter(item => 
      !revenueItems.includes(item) && 
      !costItems.includes(item) && 
      !operatingExpenseItems.includes(item) &&
      item !== 'Total Revenue' &&
      item !== 'Gross Profit' &&
      item !== 'Operating Income' &&
      item !== 'Net Income'
    )
    
    if (revenueItems.length > 0) categories['Revenue'] = revenueItems
    if (costItems.length > 0) categories['Cost of Revenue'] = costItems
    if (operatingExpenseItems.length > 0) categories['Operating Expenses'] = operatingExpenseItems
    if (otherItems.length > 0) categories['Other Income/Expenses'] = otherItems
    
    // Add summary items
    const summaryItems = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
    summaryItems.forEach(item => {
      if (allItems.includes(item)) {
        if (!categories['Summary']) categories['Summary'] = []
        categories['Summary'].push(item)
      }
    })
  } else if (statementType === 'balance') {
    // Balance Sheet categories
    const assetItems = allItems.filter(item => 
      item.toLowerCase().includes('asset') ||
      item.toLowerCase().includes('cash') ||
      item.toLowerCase().includes('inventory') ||
      item.toLowerCase().includes('receivable') ||
      item.toLowerCase().includes('property') ||
      item.toLowerCase().includes('equipment')
    )
    const liabilityItems = allItems.filter(item => 
      item.toLowerCase().includes('liabilit') ||
      item.toLowerCase().includes('debt') ||
      item.toLowerCase().includes('payable') ||
      item.toLowerCase().includes('borrowing')
    )
    const equityItems = allItems.filter(item => 
      item.toLowerCase().includes('equity') ||
      item.toLowerCase().includes('stockholder') ||
      item.toLowerCase().includes('retained')
    )
    
    if (assetItems.length > 0) categories['Assets'] = assetItems
    if (liabilityItems.length > 0) categories['Liabilities'] = liabilityItems
    if (equityItems.length > 0) categories['Equity'] = equityItems
    
    // Add summary items
    const summaryItems = ['Total Assets', 'Total Liabilities Net Minority Interest', 'Stockholders Equity']
    summaryItems.forEach(item => {
      if (allItems.includes(item)) {
        if (!categories['Summary']) categories['Summary'] = []
        categories['Summary'].push(item)
      }
    })
  } else if (statementType === 'cashflow') {
    // Cash Flow categories
    const operatingItems = allItems.filter(item => 
      item.toLowerCase().includes('operating') ||
      item.toLowerCase().includes('net income') ||
      item.toLowerCase().includes('depreciation') ||
      item.toLowerCase().includes('amortization') ||
      item.toLowerCase().includes('receivable') ||
      item.toLowerCase().includes('payable') ||
      item.toLowerCase().includes('inventory')
    )
    const investingItems = allItems.filter(item => 
      item.toLowerCase().includes('investing') ||
      item.toLowerCase().includes('capex') ||
      item.toLowerCase().includes('capital expenditure') ||
      item.toLowerCase().includes('acquisition') ||
      item.toLowerCase().includes('sale of')
    )
    const financingItems = allItems.filter(item => 
      item.toLowerCase().includes('financing') ||
      item.toLowerCase().includes('debt') ||
      item.toLowerCase().includes('issuance') ||
      item.toLowerCase().includes('repayment') ||
      item.toLowerCase().includes('dividend') ||
      item.toLowerCase().includes('stock')
    )
    
    if (operatingItems.length > 0) categories['Operating Activities'] = operatingItems
    if (investingItems.length > 0) categories['Investing Activities'] = investingItems
    if (financingItems.length > 0) categories['Financing Activities'] = financingItems
    
    // Add summary items
    const summaryItems = ['Operating Cash Flow', 'Free Cash Flow', 'Net Change In Cash']
    summaryItems.forEach(item => {
      if (allItems.includes(item)) {
        if (!categories['Summary']) categories['Summary'] = []
        categories['Summary'].push(item)
      }
    })
  }
  
  return categories
}

const toggleCategory = (statementType, category) => {
  if (expandedCategories.value[statementType].has(category)) {
    expandedCategories.value[statementType].delete(category)
  } else {
    expandedCategories.value[statementType].add(category)
  }
}

const isCategoryExpanded = (statementType, category) => {
  return expandedCategories.value[statementType].has(category)
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

const checkPaymentStatus = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    hasPaid.value = false
    checkingPayment.value = false
    return
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/payment-status', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const status = await response.json()
      hasPaid.value = status.has_paid || false
    }
  } catch (error) {
    console.error('Error checking payment status:', error)
    hasPaid.value = false
  } finally {
    checkingPayment.value = false
  }
}

const generateAllAnalyses = async () => {
  if (!companyData.value) return
  
  // Check payment status first
  if (!hasPaid.value) {
    alert('Payment required. Please verify your payment to access Company Overview & Industry Analysis generation. Visit the Research page to complete payment.')
    return
  }
  
  analyzing.value = true
  
  try {
    analysisProgress.value = 'Generating Company Overview & Industry Analysis...'
    await generateAnalysis()
    
    analysisProgress.value = 'Saving complete deep dive report...'
    const combinedReport = `# Deep Dive Analysis: ${companyData.value.company_name} (${companyData.value.ticker})

## Company Overview & Industry Analysis

${analysisReport.value || 'Not generated'}`

    
    // Ensure all sections are visible after generation
    // Force Vue to update the DOM by using nextTick
    await nextTick()
    
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
  
  // Check payment status first
  if (!hasPaid.value) {
    alert('Payment required. Please verify your payment to access Company Overview & Industry Analysis generation. Visit the Research page to complete payment.')
    return
  }
  
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('http://localhost:8000/api/agent/analyze_company', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        ticker: companyData.value.ticker,
        company_name: companyData.value.company_name,
        sector: companyData.value.sector
      })
    })
    
    if (response.status === 403) {
      const errorData = await response.json()
      alert(errorData.detail || 'Payment required to generate analysis')
      // Refresh payment status
      await checkPaymentStatus()
      return
    }
    
    if (!response.ok) throw new Error('Failed to generate analysis')
    const result = await response.json()
    analysisReport.value = result.report
  } catch (e) {
    console.error(e)
    throw e
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

const getPutCallRatio = () => {
  if (!companyData.value || !companyData.value.trading || !companyData.value.trading.options) return '-'
  
  const options = companyData.value.trading.options
  if (options.length === 0) return '-'
  
  // Sum all puts and calls volumes across all expiration dates
  const totalPutsVolume = options.reduce((sum, opt) => sum + (opt.putsVolume || 0), 0)
  const totalCallsVolume = options.reduce((sum, opt) => sum + (opt.callsVolume || 0), 0)
  
  if (totalCallsVolume === 0) return '-'
  
  const ratio = totalPutsVolume / totalCallsVolume
  return ratio.toFixed(2)
}

// PolyMarket functions
const fetchPolyMarketData = async () => {
  if (!selectedStock.value) {
    polyMarketData.value = null
    return
  }
  
  loadingPolyMarket.value = true
  polyMarketError.value = null
  
  try {
    const response = await fetch(`http://localhost:8000/api/internal/polymarket/${selectedStock.value.toUpperCase()}`)
    if (!response.ok) {
      throw new Error('Failed to fetch PolyMarket data')
    }
    polyMarketData.value = await response.json()
    
    // Render chart after data is loaded
    await nextTick()
    renderPolyMarketChart()
  } catch (err) {
    polyMarketError.value = err.message || 'Error loading PolyMarket data'
    console.error('Error fetching PolyMarket data:', err)
  } finally {
    loadingPolyMarket.value = false
  }
}

const renderPolyMarketChart = () => {
  if (!polyMarketChart.value || !polyMarketData.value) return
  
  // Destroy existing chart if it exists
  const existingChart = ChartJS.getChart(polyMarketChart.value)
  if (existingChart) {
    existingChart.destroy()
  }
  
  const labels = polyMarketData.value.targets.map(t => t.target)
  const odds = polyMarketData.value.targets.map(t => t.odds)
  
  polyMarketChartInstance = new ChartJS(polyMarketChart.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Odds (%)',
        data: odds,
        backgroundColor: odds.map(o => {
          // Color gradient: higher odds = greener, lower odds = redder
          if (o >= 40) return '#42b983'
          if (o >= 25) return '#95a5a6'
          if (o >= 15) return '#f39c12'
          return '#e74c3c'
        }),
        borderColor: '#000000',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              return `Odds: ${context.parsed.y}%`
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (value) => value + '%'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#000000'
          }
        }
      }
    }
  })
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

const institutionalHolders13F = ref([])
const loadingInstitutionalHolders = ref(false)

const handleInstitutionsClick = () => {
  holdersView.value = 'institutions'
  if (selectedStock.value && microTab.value === 'holders') {
    console.log('handleInstitutionsClick: Calling fetchInstitutionalHolders')
    fetchInstitutionalHolders()
  }
}

const fetchInstitutionalHolders = async () => {
  if (!selectedStock.value) {
    console.log('fetchInstitutionalHolders: No stock selected')
    return
  }
  
  console.log(`fetchInstitutionalHolders: Fetching for ${selectedStock.value}`)
  loadingInstitutionalHolders.value = true
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.error('fetchInstitutionalHolders: No access token found')
      institutionalHolders13F.value = []
      return
    }
    
    // Use relative URL so nginx can proxy it, or absolute if running outside Docker
    const url = `/api/filing-13f/holdings/${selectedStock.value.toUpperCase()}`
    console.log(`fetchInstitutionalHolders: Calling ${url}`)
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    console.log(`fetchInstitutionalHolders: Response status ${response.status}`)
    
    if (response.ok) {
      const data = await response.json()
      console.log(`fetchInstitutionalHolders: Received ${data.holdings?.length || 0} holdings`)
      institutionalHolders13F.value = data.holdings || []
    } else {
      const errorText = await response.text()
      console.error(`fetchInstitutionalHolders: API error ${response.status}:`, errorText)
      institutionalHolders13F.value = []
    }
  } catch (error) {
    console.error('fetchInstitutionalHolders: Exception:', error)
    institutionalHolders13F.value = []
  } finally {
    loadingInstitutionalHolders.value = false
  }
}

const getInstitutionalHolders = () => {
  // First try 13F data (new source)
  if (institutionalHolders13F.value.length > 0) {
    return institutionalHolders13F.value.map(h => ({
      'Date Reported': h['Date Reported'],
      'Holder': h['Holder'],
      'Shares': h['Shares'],
      'Value': h['Value'],
      'pctHeld': h['pctHeld'] || 0,
      'pctChange': h['pctChange'] || 0,
      'action': h['action'] || 'HOLD',
      'sharesChange': h['sharesChange'] || 0,
      'valueChange': h['valueChange'] || 0
    })).slice(0, 50)
  }
  
  // Fallback to old data structure if available
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

const getActionClass = (action) => {
  if (!action) return ''
  
  // Handle action strings (BUY, SELL, HOLD, NEW)
  if (typeof action === 'string') {
    const actionUpper = action.toUpperCase()
    if (actionUpper === 'BUY' || actionUpper === 'NEW') return 'action-buy'
    if (actionUpper === 'SELL') return 'action-sell'
    if (actionUpper === 'HOLD') return 'action-hold'
    // Legacy text parsing
    if (actionUpper.includes('SALE') || actionUpper.includes('SELL')) return 'action-sell'
    if (actionUpper.includes('PURCHASE') || actionUpper.includes('BUY')) return 'action-buy'
    if (actionUpper.includes('GIFT')) return 'action-gift'
    if (actionUpper.includes('NO CHANGE')) return 'action-no-change'
    if (actionUpper.includes('OPTION')) return 'action-option'
  }
  
  // Handle numeric pctChange (legacy support)
  if (typeof action === 'number') {
    if (action > 0) return 'action-buy'
    if (action < 0) return 'action-sell'
    return 'action-hold'
  }
  
  return 'action-other'
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

// Report functions removed - reports are now handled in /report route

// Fetch user info from API
const fetchUserInfo = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    user.value = null
    return
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      user.value = await response.json()
      localStorage.setItem('user', JSON.stringify(user.value))
    } else {
      // Token invalid, clear storage
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      user.value = null
    }
  } catch (err) {
    console.error('Failed to fetch user info:', err)
    // Fallback to localStorage
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      user.value = JSON.parse(storedUser)
    }
  }
}

onMounted(() => {
  // Load user info from localStorage first (for immediate display)
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    user.value = JSON.parse(storedUser)
  }
  
  // Fetch fresh user info from API to ensure role is correct
  fetchUserInfo()
  
  // Check payment status
  checkPaymentStatus()
  
  // Listen for login events to update user info
  const handleLoginEvent = () => {
    fetchUserInfo()
    checkPaymentStatus()
  }
  window.addEventListener('user-logged-in', handleLoginEvent)
  
  // Listen for payment verification events
  window.addEventListener('payment-verified', () => {
    checkPaymentStatus()
  })
  

  // Only load data if a stock is selected
  if (selectedStock.value) {
    loadStockData()
    fetchCompanyData()
  }
})

// Watch selectedTimePeriod to reload data when period changes
watch(selectedTimePeriod, () => {
  if (selectedStock.value) {
    loadStockData()
  }
})



</script>

<style scoped>
/* Page Layout - AlphaTrade Style */
.timeline-view {
  font-family: 'Inter', sans-serif;
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #ffffff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  border-bottom: 3px solid #000;
  padding-bottom: 1rem;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.subtitle {
  color: #666666;
  margin: 0;
  font-size: 0.875rem;
  font-style: italic;
}

.price-info {
  text-align: right;
}

.current-price-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
}

.current-price {
  font-size: 2.5rem;
  font-weight: 700;
  color: #000000;
  line-height: 1;
}

.today-change {
  font-size: 1.125rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.today-change.positive {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.today-change.negative {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.price-change {
  font-size: 0.875rem;
  color: #666666;
  margin-top: 0.5rem;
  font-weight: 500;
}

/* Stock Selector */
.stock-selector {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;
  background: #fafafa;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.stock-selector label {
  font-weight: 600;
  color: #000000;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}

.stock-selector input {
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 1rem;
  width: 300px;
  font-weight: 500;
  color: #000000;
}

.stock-selector input:focus {
  outline: none;
  border-color: #000000;
}

.stock-selector button {
  padding: 0.75rem 1.5rem;
  background-color: #000000;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: background 0.2s;
}

.stock-selector button:hover {
  background-color: #333333;
}

.stock-selector button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Chart Card */
.chart-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.chart-header h2 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #000000;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Updated Timeframe Selector */
.timeframe-selector {
  display: flex;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 2px;
}

.timeframe-selector button {
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: #666666;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 2px;
  transition: all 0.2s;
}

.timeframe-selector button.active {
  background: #ffffff;
  color: #000000;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* Events Card */
.events-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 0; 
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.events-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.events-header h2 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #000000;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Tab Selector - AlphaTrade Style */
.tab-selector {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 1.5rem;
}

.tab-btn {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-btn:hover {
  background: #ebebeb;
  color: #000;
}

.tab-btn.active {
  background: #fff;
  color: #000;
  border-bottom-color: #000;
  margin-bottom: -1px; /* Overlap border */
  border-left: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  border-top: 3px solid transparent; 
}

.tab-content {
  padding: 2rem;
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

.events-header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.creator-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.creator-selector label {
  font-size: 0.9em;
  color: #666666;
  font-weight: 500;
  white-space: nowrap;
}

.creator-select {
  padding: 8px 12px;
  border: 1px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  font-size: 0.9em;
  cursor: pointer;
  min-width: 180px;
  transition: all 0.2s;
}

.creator-select:hover {
  border-color: #3498db;
}

.creator-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
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

.company-basic-content p {
  color: #666666;
  margin: 0;
}

.analysis-section .report-content,
.analysis-section .report-content p,
.analysis-section .report-content li,
.analysis-section .report-content span,
.analysis-section .report-content div,
.analysis-section .report-content strong,
.analysis-section .report-content em,
.analysis-section .report-content a,
.analysis-section .report-content h1,
.analysis-section .report-content h2,
.analysis-section .report-content h3,
.analysis-section .report-content h4,
.analysis-section .report-content h5,
.analysis-section .report-content h6 {
  color: #000000;
}

/* Black text for report content in Notes, Operating Drivers, and Capital Structure tabs */
.micro-tab-pane .report-content,
.micro-tab-pane .report-content p,
.micro-tab-pane .report-content li,
.micro-tab-pane .report-content span,
.micro-tab-pane .report-content div,
.micro-tab-pane .report-content strong,
.micro-tab-pane .report-content em,
.micro-tab-pane .report-content a,
.micro-tab-pane .report-content h1,
.micro-tab-pane .report-content h2,
.micro-tab-pane .report-content h3,
.micro-tab-pane .report-content h4,
.micro-tab-pane .report-content h5,
.micro-tab-pane .report-content h6 {
  color: #000000;
}

/* Report with Linked Cards Styles */
.report-tab-content {
  padding: 20px;
  min-height: 500px;
}

.report-container {
  width: 100%;
  margin: 0 auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.report-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.8em;
  font-weight: 600;
}

.report-section-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.section-tab-btn {
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

.section-tab-btn:hover {
  color: #000000;
  background: #f8f9fa;
}

.section-tab-btn.active {
  color: #000000;
  border-bottom-color: #3498db;
  font-weight: 600;
}

.report-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.position-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.position-selector label {
  font-weight: 500;
  color: #000000;
}

.position-select {
  padding: 6px 12px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  background: white;
  color: #000000;
  font-size: 0.9em;
  cursor: pointer;
}

.position-select:focus {
  outline: none;
  border-color: #3498db;
}

.btn-save-report {
  padding: 8px 16px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-save-report:hover:not(:disabled) {
  background: #35a372;
}

.btn-save-report:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selection-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 16px;
  background: #e3f2fd;
  border-radius: 6px;
  border: 2px solid #3498db;
}

.btn-link-card {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-link-card:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.btn-cancel {
  padding: 8px 16px;
  border: 2px solid #cccccc;
  border-radius: 6px;
  background: transparent;
  color: #666666;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f0f0f0;
}

.report-main-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  position: relative;
}

.report-editor-area {
  flex: 1;
  min-width: 0;
  position: relative;
}

.report-editor-wrapper {
  position: relative;
}

.connector-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: visible;
}

.connector-line {
  stroke: #3498db;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.connector-line.active {
  stroke: #2980b9;
  stroke-width: 3;
  opacity: 0.8;
  stroke-dasharray: none;
}

.report-editor-header {
  margin-bottom: 15px;
}

.report-editor-header h3 {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.editor-hint {
  margin: 0;
  color: #666666;
  font-size: 0.85em;
  font-style: italic;
}

.report-editor {
  min-height: 500px;
  padding: 20px;
  border: 2px solid #cccccc;
  border-radius: 8px;
  background: #ffffff;
  color: #000000;
  font-size: 1em;
  line-height: 1.8;
  outline: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  position: relative;
  z-index: 2;
  direction: ltr;
  text-align: left;
}

.report-editor:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.report-editor :deep(.linked-sentence) {
  background-color: #e3f2fd;
  padding: 2px 4px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  display: inline;
}

.report-editor :deep(.linked-sentence:hover) {
  background-color: #bbdefb;
  box-shadow: 0 0 0 1px #3498db;
}

.report-editor :deep(.linked-sentence.active) {
  background-color: #90caf9;
  box-shadow: 0 0 0 2px #3498db;
  animation: pulse-highlight 1s ease-in-out;
}

@keyframes pulse-highlight {
  0%, 100% {
    box-shadow: 0 0 0 2px #3498db;
  }
  50% {
    box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.5);
  }
}

.flashcard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.flashcard-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.8em;
  font-weight: 600;
}

.flashcard-actions {
  display: flex;
  gap: 10px;
}

.btn-add-card,
.btn-complete {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-card {
  background: #3498db;
  color: white;
}

.btn-add-card:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.btn-complete {
  background: #42b983;
  color: white;
}

.btn-complete:hover {
  background: #35a372;
  transform: translateY(-1px);
}

.empty-deck {
  text-align: center;
  padding: 60px 20px;
  color: #666666;
  font-size: 1.1em;
}

.flashcard-viewer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.card-counter {
  font-size: 0.9em;
  color: #666666;
  font-weight: 500;
}

.flashcard-wrapper {
  width: 100%;
  max-width: 600px;
  height: 400px;
  perspective: 1000px;
}

.flashcard {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
}

.flashcard-side {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid #cccccc;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backface-visibility: hidden;
  transform: rotateY(0deg);
}


.card-label {
  padding: 12px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
  color: #666666;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-textarea {
  flex: 1;
  padding: 20px;
  border: none;
  outline: none;
  resize: none;
  font-size: 1.1em;
  line-height: 1.6;
  color: #000000;
  font-family: inherit;
  background: transparent;
}

.card-textarea::placeholder {
  color: #999999;
}

.flashcard-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-top: 20px;
}

.nav-btn {
  padding: 12px 24px;
  border: 2px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.card-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn-add-card {
  padding: 10px 20px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-card:hover {
  background: #2980b9;
  border-color: #2980b9;
  transform: translateY(-1px);
}

.btn-delete-card {
  padding: 10px 20px;
  border: 2px solid #e74c3c;
  border-radius: 6px;
  background: transparent;
  color: #e74c3c;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete-card:hover {
  background: #e74c3c;
  color: white;
}

/* Linked Cards Sidebar Styles */
.linked-cards-sidebar {
  width: 350px;
  background: #f8f9fa;
  border-left: 1px solid #cccccc;
  padding: 20px;
  border-radius: 8px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  flex-shrink: 0;
  position: relative;
}

.linked-cards-sidebar h3 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.no-cards {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
  font-size: 0.9em;
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.linked-card-item {
  padding: 12px;
  background: #ffffff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.linked-card-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
}

.linked-card-item.active {
  background: #e3f2fd;
  border-color: #3498db;
  border-width: 2px;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.card-sentence-preview {
  font-size: 0.85em;
  color: #666666;
  font-style: italic;
  line-height: 1.4;
  flex: 1;
}

.btn-delete-small {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #e74c3c;
  font-size: 1.2em;
  font-weight: bold;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.btn-delete-small:hover {
  background: #fee;
  color: #c0392b;
}

.card-content-editor {
  margin-top: 8px;
}

.card-textarea-small {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  font-size: 0.9em;
  line-height: 1.5;
  color: #000000;
  font-family: inherit;
  resize: vertical;
  outline: none;
}

.card-textarea-small:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.card-textarea-small::placeholder {
  color: #999999;
}

/* Report History Styles */
.report-upload-section {
  padding: 20px 0;
}

.upload-header {
  margin-bottom: 30px;
}

.upload-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.upload-hint {
  color: #666666;
  font-size: 0.9em;
  margin: 0;
}

.upload-area {
  border: 2px dashed #cccccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f0f7ff;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 20px;
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 15px;
}

.upload-text {
  color: #000000;
  font-size: 1em;
}

.upload-text strong {
  color: #3498db;
  font-weight: 600;
}

.upload-formats {
  color: #666666;
  font-size: 0.85em;
  margin-top: 5px;
  display: block;
}

.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
}

.upload-progress p {
  margin: 0 0 10px 0;
  color: #1976d2;
  font-weight: 500;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s;
  border-radius: 4px;
}

.upload-error {
  margin-top: 20px;
  padding: 15px;
  background: #ffebee;
  border: 1px solid #e74c3c;
  border-radius: 6px;
  color: #c62828;
}

.upload-success {
  margin-top: 20px;
  padding: 15px;
  background: #e8f5e9;
  border: 1px solid #42b983;
  border-radius: 6px;
  color: #2e7d32;
}

.upload-success p {
  margin: 5px 0;
}

.upload-filename {
  font-weight: 600;
  color: #1b5e20;
}

.report-history-section {
  padding: 20px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.history-header h3 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.btn-refresh {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: #3498db;
  color: white;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
}

.empty-history {
  text-align: center;
  padding: 60px 20px;
  color: #666666;
}

.hint-text {
  font-size: 0.9em;
  color: #999999;
  margin-top: 10px;
}

/* Upload Section Styles */
.report-upload-section {
  padding: 20px 0;
}

.upload-header {
  margin-bottom: 30px;
}

.upload-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.upload-hint {
  color: #666666;
  font-size: 0.9em;
  margin: 0;
}

.upload-area {
  border: 2px dashed #cccccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f0f7ff;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 20px;
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 15px;
}

.upload-text {
  color: #000000;
  font-size: 1em;
}

.upload-text strong {
  color: #3498db;
  font-weight: 600;
}

.upload-formats {
  color: #666666;
  font-size: 0.85em;
  margin-top: 5px;
  display: block;
}

.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
}

.upload-progress p {
  margin: 0 0 10px 0;
  color: #1976d2;
  font-weight: 500;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s;
  border-radius: 4px;
}

.upload-error {
  margin-top: 20px;
  padding: 15px;
  background: #ffebee;
  border: 1px solid #e74c3c;
  border-radius: 6px;
  color: #c62828;
}

.upload-success {
  margin-top: 20px;
  padding: 15px;
  background: #e8f5e9;
  border: 1px solid #42b983;
  border-radius: 6px;
  color: #2e7d32;
}

.upload-success p {
  margin: 5px 0;
}

.upload-filename {
  font-weight: 600;
  color: #1b5e20;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-item {
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: #ffffff;
  transition: all 0.2s;
  cursor: pointer;
}

.history-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
  transform: translateY(-2px);
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.history-item-info h4 {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
}

.history-date {
  margin: 0;
  color: #666666;
  font-size: 0.85em;
}

.history-item-actions {
  display: flex;
  gap: 10px;
}

.btn-load-report {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-load-report:hover {
  background: #2980b9;
  border-color: #2980b9;
}

.btn-delete-history {
  padding: 8px 16px;
  border: 2px solid #e74c3c;
  border-radius: 6px;
  background: transparent;
  color: #e74c3c;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete-history:hover {
  background: #e74c3c;
  color: white;
}

.history-item-preview {
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.history-item-preview p {
  margin: 0;
  color: #666666;
  font-size: 0.9em;
  line-height: 1.6;
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

.event-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.delete-event-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.6;
}

.delete-event-btn:hover {
  opacity: 1;
  background: #fee;
  transform: scale(1.1);
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

.overview-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.tenk-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.section-header h4 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.refresh-btn {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #3498db;
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.analysis-section-wrapper {
  flex: 1;
  min-width: 0;
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

.detailed-tables .category-header {
  background-color: #f8f9fa;
  cursor: pointer;
  transition: background-color 0.2s;
}

.detailed-tables .category-header:hover {
  background-color: #e9ecef;
}

.detailed-tables .category-name {
  font-weight: 600;
  color: #000000;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detailed-tables .expand-icon {
  display: inline-block;
  width: 16px;
  text-align: center;
  color: #3498db;
  font-size: 0.9em;
}

.detailed-tables .category-item {
  background-color: #ffffff;
}

.detailed-tables .category-item .item-name {
  padding-left: 40px;
  font-weight: 400;
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

.trade-action.action-buy {
  color: #10b981;
  font-weight: 600;
}

.trade-action.action-sell {
  color: #ef4444;
  font-weight: 600;
}

.trade-action.action-hold {
  color: #6b7280;
}

.trade-action {
  font-weight: 600;
  text-transform: uppercase;
}

.trade-action.action-buy {
  color: #10b981;
  font-weight: 600;
}

.trade-action.action-purchase {
  color: #3498db;
}

.trade-action.action-sell {
  color: #e74c3c;
}

.trade-action.action-hold {
  color: #6b7280;
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

/* Productivity Tab Styles */
.productivity-tab-content {
    padding: 20px 0;
}

.content-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.info-card {
    border: 1px solid #cccccc;
    padding: 30px;
    border-radius: 12px;
    background: #ffffff;
    color: #000000;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.5em;
    color: #000000;
    font-weight: 600;
}

.info-card p {
    margin: 12px 0;
    line-height: 1.6;
    color: #666666;
}

.coming-soon {
    font-style: italic;
    color: #999999;
    margin-top: 20px;
}

/* PolyMarket Styles */
.polymarket-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.polymarket-warning {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px 20px;
    color: #856404;
    font-size: 0.95em;
    line-height: 1.6;
}

.polymarket-warning strong {
    color: #856404;
    font-weight: 600;
}

.polymarket-header {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
}

.polymarket-header h3 {
    margin: 0 0 10px 0;
    color: #000000;
    font-size: 1.5em;
    font-weight: 600;
}

.polymarket-question {
    margin: 0;
    color: #666666;
    font-size: 1em;
}

.polymarket-chart-container {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    height: 400px;
    position: relative;
}

.polymarket-table {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    overflow-x: auto;
}

.polymarket-table table {
    width: 100%;
    border-collapse: collapse;
}

.polymarket-table thead {
    background: #f8f9fa;
}

.polymarket-table th {
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    color: #000000;
    border-bottom: 2px solid #cccccc;
}

.polymarket-table td {
    padding: 12px 15px;
    color: #000000;
    border-bottom: 1px solid #e0e0e0;
}

.polymarket-table tbody tr:hover {
    background: #f8f9fa;
}

.odds-value {
    font-weight: 600;
    font-size: 1.1em;
    color: #3498db;
}

.loading-state {
    text-align: center;
    padding: 40px;
    color: #666666;
}

.error-message {
    background: #ffe6e6;
    border: 1px solid #ff9999;
    padding: 20px;
    border-radius: 8px;
    color: #cc0000;
}

/* Overview Layout Styles */
.overview-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.tenk-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.section-header h4 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.refresh-btn {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #3498db;
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #cccccc !important;
  color: #666666 !important;
  border-color: #cccccc !important;
}

.payment-notice {
  margin-top: 10px;
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 0.9em;
}

.tenk-content {
  display: flex;
  flex-direction: column;
}

.tenk-full-html {
  color: #000000;
  font-size: 0.95em;
  line-height: 1.8;
  padding: 20px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  max-width: 100%;
  overflow-x: auto;
}

.tenk-full-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 0.9em;
}

.tenk-full-html :deep(table th),
.tenk-full-html :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.tenk-full-html :deep(table th) {
  background-color: #f8f9fa;
  font-weight: 600;
}

.tenk-full-html :deep(p) {
  margin: 10px 0;
  line-height: 1.6;
}

.tenk-full-html :deep(h1),
.tenk-full-html :deep(h2),
.tenk-full-html :deep(h3),
.tenk-full-html :deep(h4),
.tenk-full-html :deep(h5),
.tenk-full-html :deep(h6) {
  margin: 20px 0 10px 0;
  font-weight: 600;
  color: #000000;
}

.tenk-full-html :deep(ul),
.tenk-full-html :deep(ol) {
  margin: 10px 0;
  padding-left: 30px;
}

.tenk-full-html :deep(li) {
  margin: 5px 0;
  line-height: 1.6;
}

.tenk-full-html :deep(strong),
.tenk-full-html :deep(b) {
  font-weight: 600;
  color: #000000;
}

.tenk-full-html :deep(em),
.tenk-full-html :deep(i) {
  font-style: italic;
}

.analysis-section-wrapper {
  flex: 1;
  min-width: 0;
}

.analysis-report-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.analysis-report-content {
  flex: 1;
  overflow-y: auto;
  margin-top: 10px;
}

.analysis-report-section .progress-indicator {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 6px;
  margin: 15px 0;
  font-weight: 500;
  color: #2e7d32;
  text-align: center;
}

.analysis-html-content {
  color: #000000;
  font-size: 0.95em;
  line-height: 1.8;
  padding: 0;
  background: transparent;
}

.analysis-html-content :deep(h1),
.analysis-html-content :deep(h2),
.analysis-html-content :deep(h3),
.analysis-html-content :deep(h4),
.analysis-html-content :deep(h5),
.analysis-html-content :deep(h6) {
  margin: 20px 0 10px 0;
  font-weight: 600;
  color: #000000;
}

.analysis-html-content :deep(h1) {
  font-size: 1.8em;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

.analysis-html-content :deep(h2) {
  font-size: 1.5em;
  margin-top: 30px;
}

.analysis-html-content :deep(h3) {
  font-size: 1.3em;
}

.analysis-html-content :deep(p) {
  margin: 10px 0;
  line-height: 1.8;
  color: #000000;
}

.analysis-html-content :deep(ul),
.analysis-html-content :deep(ol) {
  margin: 15px 0;
  padding-left: 30px;
}

.analysis-html-content :deep(li) {
  margin: 8px 0;
  line-height: 1.8;
  color: #000000;
}

.analysis-html-content :deep(strong),
.analysis-html-content :deep(b) {
  font-weight: 600;
  color: #000000;
}

.analysis-html-content :deep(em),
.analysis-html-content :deep(i) {
  font-style: italic;
}

.analysis-html-content :deep(blockquote) {
  border-left: 4px solid #3498db;
  padding-left: 15px;
  margin: 15px 0;
  color: #666666;
  font-style: italic;
}

.analysis-html-content :deep(code) {
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.analysis-html-content :deep(pre) {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 15px 0;
}

.analysis-html-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.analysis-html-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 0.9em;
}

.analysis-html-content :deep(table th),
.analysis-html-content :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.analysis-html-content :deep(table th) {
  background-color: #f8f9fa;
  font-weight: 600;
}

.analysis-html-content :deep(a) {
  color: #3498db;
  text-decoration: none;
}

.analysis-html-content :deep(a:hover) {
  text-decoration: underline;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
  font-style: italic;
}

</style>


