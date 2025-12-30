<template>
  <div class="micro-view">
    <h1>Micro Economics: Company Deep Dive</h1>
    
    <div class="search-bar">
      <input v-model="ticker" placeholder="Enter Ticker (e.g., AAPL)" @keyup.enter="fetchData" />
      <button @click="fetchData">Search</button>
    </div>

    <div v-if="loading" class="loading">Loading Data...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="data" class="company-data">
        <div class="header">
            <h2>{{ data.company_name }} ({{ data.ticker }})</h2>
            <div class="price-info">
                <span class="price">${{ data.price }}</span>
                <span class="sector">{{ data.sector }} | {{ data.industry }}</span>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <button :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'" :data-text="'Overview'">Overview</button>
            <button :class="{ active: activeTab === 'financials' }" @click="activeTab = 'financials'" :data-text="'Financial Statements'">Financial Statements</button>
            <button :class="{ active: activeTab === 'ratios' }" @click="activeTab = 'ratios'" :data-text="'Ratios'">Ratios</button>
            <button :class="{ active: activeTab === 'filings' }" @click="activeTab = 'filings'" :data-text="'Filings'">Filings</button>
            <button :class="{ active: activeTab === 'holders' }" @click="activeTab = 'holders'" :data-text="'Holders'">Holders</button>
            <button :class="{ active: activeTab === 'trading' }" @click="activeTab = 'trading'" :data-text="'Trading'">Trading</button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
            
            <!-- Overview -->
            <div v-if="activeTab === 'overview'" class="tab-pane">
                 <!-- Standard Company Info (if any) or just blank/placeholder if it was only AI before -->
                 <!-- Assuming there is standard data content below or we just show nothing specific for now -->
            </div>



            <!-- Financial Statements (Unified) -->
            <div v-if="activeTab === 'financials'" class="tab-pane">
                <div class="financials-header">
                    <h3>Financial Statements Overview</h3>
                    <div class="period-selector">
                        <button 
                            :class="{ active: financialPeriod === 'annual' }" 
                            @click="financialPeriod = 'annual'"
                        >
                            Annual
                        </button>
                        <button 
                            :class="{ active: financialPeriod === 'quarterly' }" 
                            @click="financialPeriod = 'quarterly'"
                        >
                            Quarterly
                        </button>
                    </div>
                </div>
                
                <!-- Key Metrics Summary -->
                <h4>LTM Snapshot</h4>
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
                    <!-- Revenue & Profitability Trends -->
                    <div class="chart-section">
                        <h4>Revenue & Profitability Trends ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</h4>
                        <div class="chart-container">
                            <canvas ref="revenueProfitChart"></canvas>
                        </div>
                    </div>

                    <!-- Cash Flow Trends -->
                    <div class="chart-section">
                        <h4>Cash Flow Analysis ({{ financialPeriod === 'annual' ? 'Annual' : 'Quarterly' }})</h4>
                        <div class="chart-container">
                            <canvas ref="cashflowChart"></canvas>
                        </div>
                    </div>

                    <!-- Balance Sheet Composition -->
                    <div class="chart-section">
                        <h4>Balance Sheet Composition (Latest)</h4>
                        <div class="balance-composition">
                            <div class="composition-chart">
                                <h5>Assets</h5>
                                <canvas ref="assetsChart"></canvas>
                            </div>
                            <div class="composition-chart">
                                <h5>Liabilities & Equity</h5>
                                <canvas ref="liabilitiesChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detailed Tables (Collapsible) -->
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

            <!-- Ratios -->
            <div v-if="activeTab === 'ratios'" class="tab-pane">
                <div class="ratios-grid">
                    <div class="ratio-card">
                        <h4>Profitability</h4>
                        <p>Gross Margin: {{ formatPercent(data.ratios.profitability.grossMargins) }}</p>
                        <p>Operating Margin: {{ formatPercent(data.ratios.profitability.operatingMargins) }}</p>
                        <p>EBITDA Margin: {{ formatPercent(data.ratios.profitability.ebitdaMargins) }}</p>
                        <p>Net Margin: {{ formatPercent(data.ratios.profitability.netMargin) }}</p>
                        <p>ROA: {{ formatPercent(data.ratios.profitability.returnOnAssets) }}</p>
                        <p>ROE: {{ formatPercent(data.ratios.profitability.returnOnEquity) }}</p>
                        <p>ROIC: {{ formatPercent(data.ratios.profitability.returnOnInvestedCapital) }}</p>
                        <p>FCF Yield: {{ formatPercent(data.ratios.profitability.fcfYield) }}</p>
                    </div>
                    <div class="ratio-card">
                        <h4>Liquidity & Solvency</h4>
                        <p>Current Ratio: {{ formatRatio(data.ratios.liquidity.currentRatio) }}</p>
                        <p>Quick Ratio: {{ formatRatio(data.ratios.liquidity.quickRatio) }}</p>
                        <p>Debt/Equity: {{ formatRatio(data.ratios.liquidity.debtToEquity) }}</p>
                        <p>Debt/EBITDA: {{ formatRatio(data.ratios.liquidity.debtToEbitda) }}</p>
                        <p>Interest Coverage: {{ formatRatio(data.ratios.liquidity.interestCoverage) }}</p>
                    </div>
                    <div class="ratio-card">
                        <h4>Efficiency</h4>
                        <p>Inventory Turnover: {{ formatRatio(data.ratios.efficiency.inventoryTurnover) }}</p>
                        <p>Days Sales Outstanding: {{ formatDays(data.ratios.efficiency.daysSalesOutstanding) }}</p>
                        <p>Days Payable Outstanding: {{ formatDays(data.ratios.efficiency.daysPayableOutstanding) }}</p>
                        <p>Asset Turnover: {{ formatRatio(data.ratios.efficiency.assetTurnover) }}</p>
                        <p>Working Capital: {{ formatNumber(data.ratios.efficiency.workingCapital) }}</p>
                    </div>
                    <div class="ratio-card">
                        <h4>Valuation</h4>
                        <p>P/E (Trailing): {{ formatRatio(data.ratios.valuation.trailingPE) }}</p>
                        <p>P/E (Forward): {{ formatRatio(data.ratios.valuation.forwardPE) }}</p>
                        <p>P/B: {{ formatRatio(data.ratios.valuation.priceToBook) }}</p>
                        <p>EV/EBITDA: {{ formatRatio(data.ratios.valuation.enterpriseToEbitda) }}</p>
                        <p>P/S: {{ formatRatio(data.ratios.valuation.priceToSales) }}</p>
                        <p>EV/Revenue: {{ formatRatio(data.ratios.valuation.evToRevenue) }}</p>
                    </div>
                </div>
            </div>

            <!-- Notes & Disclosures -->
            <div v-if="activeTab === 'notes'" class="tab-pane">
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

            <!-- Operating Drivers -->
            <div v-if="activeTab === 'drivers'" class="tab-pane">
                <div class="ai-section">
                    <button @click="generateDriversAnalysis" :disabled="analyzingDrivers" class="ai-btn">
                        {{ analyzingDrivers ? 'Generating Analysis...' : '⚙️ Generate Operating Drivers Analysis' }}
                    </button>
                    
                    <div v-if="driversReport">
                        <div class="report-content" v-html="renderMarkdown(driversReport)"></div>
                        
                        <!-- Operating Metrics Visualization -->
                        <div v-if="data" class="metrics-viz">
                            <h4>Key Operating Metrics (LTM)</h4>
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
                                    <div class="metric-value">{{ formatPercent(data.ratios.profitability.operatingMargins) }}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Asset Turnover</div>
                                    <div class="metric-value">{{ formatRatio(data.ratios.efficiency.assetTurnover) }}x</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Inventory Turnover</div>
                                    <div class="metric-value">{{ formatRatio(data.ratios.efficiency.inventoryTurnover) }}x</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Days Sales Outstanding</div>
                                    <div class="metric-value">{{ formatDays(data.ratios.efficiency.daysSalesOutstanding) }}</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Working Capital</div>
                                    <div class="metric-value">{{ formatNumber(data.ratios.efficiency.workingCapital) }}</div>
                                </div>
                            </div>
                            
                            <!-- Efficiency Comparison -->
                            <div class="efficiency-chart">
                                <h5>Efficiency Metrics</h5>
                                <div class="bar-chart">
                                    <div class="chart-bar">
                                        <div class="bar-label">Inventory Turnover</div>
                                        <div class="bar-container">
                                            <div class="bar-fill" :style="{ width: Math.min((data.ratios.efficiency.inventoryTurnover || 0) * 10, 100) + '%' }"></div>
                                            <span class="bar-value">{{ formatRatio(data.ratios.efficiency.inventoryTurnover) }}</span>
                                        </div>
                                    </div>
                                    <div class="chart-bar">
                                        <div class="bar-label">Asset Turnover</div>
                                        <div class="bar-container">
                                            <div class="bar-fill" :style="{ width: Math.min((data.ratios.efficiency.assetTurnover || 0) * 50, 100) + '%' }"></div>
                                            <span class="bar-value">{{ formatRatio(data.ratios.efficiency.assetTurnover) }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-else class="info-message">
                        Generate the Complete Deep Dive from the Overview tab to see this analysis.
                    </div>
                </div>
            </div>

            <!-- Capital Structure -->
            <div v-if="activeTab === 'capital'" class="tab-pane">
                <div class="ai-section">
                    <button @click="generateCapitalAnalysis" :disabled="analyzingCapital" class="ai-btn">
                        {{ analyzingCapital ? 'Generating Analysis...' : '💰 Generate Capital Structure Analysis' }}
                    </button>
                    
                    <div v-if="capitalReport">
                        <div class="report-content" v-html="renderMarkdown(capitalReport)"></div>
                        
                        <!-- Capital Structure Visualization -->
                        <div v-if="data" class="capital-viz">
                            <h4>Capital Structure Metrics</h4>
                            <div class="metrics-grid">
                                <div class="metric-card highlight">
                                    <div class="metric-label">Debt/Equity</div>
                                    <div class="metric-value">{{ formatRatio(data.ratios.liquidity.debtToEquity) }}</div>
                                </div>
                                <div class="metric-card highlight">
                                    <div class="metric-label">Debt/EBITDA</div>
                                    <div class="metric-value">{{ formatRatio(data.ratios.liquidity.debtToEbitda) }}x</div>
                                </div>
                                <div class="metric-card highlight">
                                    <div class="metric-label">Interest Coverage</div>
                                    <div class="metric-value">{{ formatRatio(data.ratios.liquidity.interestCoverage) }}x</div>
                                </div>
                                <div class="metric-card highlight">
                                    <div class="metric-label">FCF Yield</div>
                                    <div class="metric-value">{{ formatPercent(data.ratios.profitability.fcfYield) }}</div>
                                </div>
                            </div>
                            
                            <!-- Liquidity Analysis -->
                            <div class="liquidity-section">
                                <h5>Liquidity & Solvency Analysis</h5>
                                <div class="leverage-bar">
                                    <div class="bar-label">Current Ratio: {{ formatRatio(data.ratios.liquidity.currentRatio) }}</div>
                                    <div class="bar-container">
                                        <div class="bar-fill liquidity" :style="{ width: Math.min((data.ratios.liquidity.currentRatio || 0) * 50, 100) + '%' }"></div>
                                    </div>
                                    <div class="bar-benchmark">Benchmark: 2.0</div>
                                </div>
                                <div class="leverage-bar">
                                    <div class="bar-label">Quick Ratio: {{ formatRatio(data.ratios.liquidity.quickRatio) }}</div>
                                    <div class="bar-container">
                                        <div class="bar-fill liquidity" :style="{ width: Math.min((data.ratios.liquidity.quickRatio || 0) * 50, 100) + '%' }"></div>
                                    </div>
                                    <div class="bar-benchmark">Benchmark: 1.0</div>
                                </div>
                                <div class="leverage-bar">
                                    <div class="bar-label">Debt/Equity: {{ formatRatio(data.ratios.liquidity.debtToEquity) }}</div>
                                    <div class="bar-container">
                                        <div class="bar-fill debt" :style="{ width: Math.min((data.ratios.liquidity.debtToEquity || 0) * 20, 100) + '%' }"></div>
                                    </div>
                                    <div class="bar-benchmark">Lower is better</div>
                                </div>
                            </div>
                            
                            <!-- Profitability vs Leverage -->
                            <div class="profitability-leverage">
                                <h5>Profitability vs. Leverage</h5>
                                <div class="comparison-grid">
                                    <div class="comparison-item">
                                        <div class="comparison-label">ROE</div>
                                        <div class="comparison-value">{{ formatPercent(data.ratios.profitability.returnOnEquity) }}</div>
                                    </div>
                                    <div class="comparison-item">
                                        <div class="comparison-label">ROIC</div>
                                        <div class="comparison-value">{{ formatPercent(data.ratios.profitability.returnOnInvestedCapital) }}</div>
                                    </div>
                                    <div class="comparison-item">
                                        <div class="comparison-label">Debt/EBITDA</div>
                                        <div class="comparison-value">{{ formatRatio(data.ratios.liquidity.debtToEbitda) }}x</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-else class="info-message">
                        Generate the Complete Deep Dive from the Overview tab to see this analysis.
                    </div>
                </div>
            </div>

            <!-- Filings -->
            <div v-if="activeTab === 'filings'" class="tab-pane">
                <h3>SEC Filings</h3>
                <div v-if="data.filings && data.filings.length > 0" class="filings-container">
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

            <!-- Holders -->
            <div v-if="activeTab === 'holders'" class="tab-pane">
                <h3>Trade Log</h3>
                
                <!-- Tab selector for All/Institutions/Insider -->
                <div class="trade-log-tabs">
                    <button :class="{ active: holdersView === 'all' }" @click="holdersView = 'all'">All</button>
                    <button :class="{ active: holdersView === 'institutions' }" @click="holdersView = 'institutions'">Institutions</button>
                    <button :class="{ active: holdersView === 'insider' }" @click="holdersView = 'insider'">Insider</button>
                </div>

                <!-- Insider Transactions Table -->
                <div v-if="holdersView === 'insider' || holdersView === 'all'" class="trade-log-container">
                    <h4 v-if="holdersView === 'all'" class="section-heading">Insider Transactions</h4>
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
                                <td class="trade-shares">{{ formatNumber(transaction.Shares) }}</td>
                                <td class="trade-value">{{ formatNumber(transaction.Value) }}</td>
                                <td class="trade-holdings">{{ transaction.Ownership }}</td>
                                <td class="trade-party">{{ transaction.Position || 'Officer' }}</td>
                                <td class="trade-insider">{{ transaction.Insider }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-else class="no-data">No insider transaction data available</div>
                </div>

                <!-- Institutional Holders Table -->
                <div v-if="holdersView === 'institutions' || holdersView === 'all'" class="trade-log-container">
                    <h4 v-if="holdersView === 'all'" class="section-heading">Institutional Holders</h4>
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
                                <td class="trade-shares">{{ formatNumber(holder.Shares) }}</td>
                                <td class="trade-value">{{ formatCurrency(holder.Value) }}</td>
                                <td class="trade-holdings">{{ formatPercent(holder.pctHeld) }}</td>
                                <td class="trade-action" :class="getChangeClass(holder.pctChange)">
                                    {{ formatPercentChange(holder.pctChange) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-else class="no-data">Institutional holder data will be available soon</div>
                </div>
            </div>

            <!-- Trading -->
            <div v-if="activeTab === 'trading'" class="tab-pane">
                <div class="ratios-grid">
                    <div class="ratio-card">
                        <h4>Short Interest</h4>
                        <p>Short Ratio: {{ data.trading.shortRatio }}</p>
                        <p>Short % of Float: {{ formatPercent(data.trading.shortPercentOfFloat) }}</p>
                        <p>Shares Short: {{ formatNumber(data.trading.sharesShort) }}</p>
                    </div>
                    <div class="ratio-card">
                        <h4>Volume & Price</h4>
                        <p>Avg Volume: {{ formatNumber(data.trading.averageVolume) }}</p>
                        <p>52W High: ${{ data.trading.fiftyTwoWeekHigh }}</p>
                        <p>52W Low: ${{ data.trading.fiftyTwoWeekLow }}</p>
                        <p>Beta: {{ data.trading.beta }}</p>
                    </div>
                </div>
                
                <!-- Options Charts -->
                <div v-if="data.trading.options && data.trading.options.length > 0" class="options-charts-container">
                    <!-- Total Volume & Open Interest Chart -->
                    <div class="options-chart-section">
                        <h3>Total Volume & Open Interest by Expiry Date</h3>
                        <div class="chart-container">
                            <canvas ref="optionsVolumeChart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Calls & Puts Volume Chart -->
                    <div class="options-chart-section">
                        <h3>Calls & Puts Volume by Expiry Date</h3>
                        <div class="chart-container">
                            <canvas ref="optionsCallsPutsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, onMounted, onActivated, nextTick, watch, computed } from 'vue';
import { marked } from 'marked';
import {
  Chart,
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

defineOptions({
  name: 'MicroView'
})

Chart.register(
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
);

const ticker = ref('');
const data = ref(null);
const loading = ref(false);
const error = ref(null);
const activeTab = ref('overview');
const financialPeriod = ref('annual'); // 'annual' or 'quarterly'

const analyzing = ref(false);
const analysisReport = ref(null);
const analyzingNotes = ref(false);
const notesReport = ref(null);
const analyzingDrivers = ref(false);
const driversReport = ref(null);
const analyzingCapital = ref(false);
const capitalReport = ref(null);
const analysisProgress = ref('');
const hasPaid = ref(false);
const checkingPayment = ref(true);


// Chart refs
const revenueProfitChart = ref(null);
const cashflowChart = ref(null);
const assetsChart = ref(null);
const liabilitiesChart = ref(null);
const optionsVolumeChart = ref(null);
const optionsCallsPutsChart = ref(null);

// Chart instances
let revenueProfitChartInstance = null;
let cashflowChartInstance = null;
let assetsChartInstance = null;
let liabilitiesChartInstance = null;
let optionsVolumeChartInstance = null;
let optionsCallsPutsChartInstance = null;

// Watch for data changes and render charts
watch([data, activeTab, financialPeriod], async ([newData, newTab, newPeriod]) => {
    if (newData && newTab === 'financials') {
        await nextTick();
        renderFinancialCharts();
    }
    if (newData && newTab === 'trading') {
        await nextTick();
        renderOptionsVolumeChart();
        renderOptionsCallsPutsChart();
    }
});

// Re-render charts when component is activated (keep-alive)
onActivated(async () => {
    if (data.value) {
        await nextTick();
        if (activeTab.value === 'financials') {
            renderFinancialCharts();
        } else if (activeTab.value === 'trading') {
            renderOptionsVolumeChart();
            renderOptionsCallsPutsChart();
        }
    }
});

// Check payment status on mount
onMounted(() => {
    checkPaymentStatus()
    
    // Listen for payment verification events
    window.addEventListener('payment-verified', () => {
        checkPaymentStatus()
    })
});

const fetchData = async () => {
  if (!ticker.value) return;
  loading.value = true;
  error.value = null;
  data.value = null;
  analysisReport.value = null;
  notesReport.value = null;
  driversReport.value = null;
  capitalReport.value = null;
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/internal/micro/${ticker.value}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    data.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

// Watch for data changes and render charts
watch([data, activeTab, financialPeriod], async ([newData, newTab, newPeriod]) => {
    if (newData && newTab === 'financials') {
        await nextTick();
        renderFinancialCharts();
    }
    if (newData && newTab === 'trading') {
        await nextTick();
        renderOptionsVolumeChart();
        renderOptionsCallsPutsChart();
    }
});

const saveReport = async (title, content, type) => {
    if (!data.value) return;
    try {
        await fetch(`${API_BASE_URL}/api/reports/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: content,
                report_type: type,
                ticker: data.value.ticker
            })
        });
    } catch (e) {
        console.error("Failed to save report", e);
    }
};

const generateAllAnalyses = async () => {
    if (!data.value) return;
    
    // Check payment status first
    if (!hasPaid.value) {
        alert('Payment required. Please verify your payment to access Company Overview & Industry Analysis generation. Visit the Research page to complete payment.')
        return
    }
    
    analyzing.value = true;
    
    try {
        // Generate Company Overview
        analysisProgress.value = 'Generating Company Overview & Industry Analysis...';
        await generateAnalysis();
        
        // Generate Notes & Disclosures
        analysisProgress.value = 'Generating Notes & Disclosures Analysis...';
        await generateNotesAnalysis();
        
        // Generate Operating Drivers
        analysisProgress.value = 'Generating Operating Drivers Analysis...';
        await generateDriversAnalysis();
        
        // Generate Capital Structure
        analysisProgress.value = 'Generating Capital Structure Analysis...';
        await generateCapitalAnalysis();
        
        // Save combined report
        analysisProgress.value = 'Saving complete deep dive report...';
        const combinedReport = `# Deep Dive Analysis: ${data.value.company_name} (${data.value.ticker})

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

${capitalReport.value || 'Not generated'}`;

        await saveReport(
            `Deep Dive: ${data.value.company_name} (${data.value.ticker})`,
            combinedReport,
            'deep_dive'
        );
        
        analysisProgress.value = 'Complete!';
    } catch (e) {
        console.error(e);
        alert("Failed to generate complete analysis");
    } finally {
        analyzing.value = false;
        setTimeout(() => { analysisProgress.value = ''; }, 2000);
    }
};

const checkPaymentStatus = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
        hasPaid.value = false
        checkingPayment.value = false
        return
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/payment-status`, {
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

const generateAnalysis = async () => {
    if (!data.value) return;
    
    // Check payment status first
    if (!hasPaid.value) {
        alert('Payment required. Please verify your payment to access Company Overview & Industry Analysis generation. Visit the Research page to complete payment.')
        return
    }
    
    try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${API_BASE_URL}/api/agent/analyze_company`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                ticker: data.value.ticker,
                company_name: data.value.company_name,
                sector: data.value.sector
            })
        });
        
        if (response.status === 403) {
            const errorData = await response.json()
            alert(errorData.detail || 'Payment required to generate analysis')
            // Refresh payment status
            await checkPaymentStatus()
            return
        }
        
        if (!response.ok) throw new Error('Failed to generate analysis');
        const result = await response.json();
        analysisReport.value = result.report;
        await saveReport(`Company Overview: ${data.value.company_name}`, result.report, 'company_overview');
    } catch (e) {
        console.error(e);
        throw e;
    }
};

const generateNotesAnalysis = async () => {
    if (!data.value) return;
    analyzingNotes.value = true;
    try {
        const response = await fetch(`${API_BASE_URL}/api/agent/analyze_notes_disclosures`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker: data.value.ticker,
                company_name: data.value.company_name,
                sector: data.value.sector
            })
        });
        if (!response.ok) throw new Error('Failed to generate analysis');
        const result = await response.json();
        notesReport.value = result.report;
        await saveReport(`Notes & Disclosures: ${data.value.company_name}`, result.report, 'notes_disclosures');
    } catch (e) {
        console.error(e);
        if (!analyzing.value) alert("Failed to generate notes analysis");
        throw e;
    } finally {
        analyzingNotes.value = false;
    }
};

const generateDriversAnalysis = async () => {
    if (!data.value) return;
    analyzingDrivers.value = true;
    try {
        const response = await fetch(`${API_BASE_URL}/api/agent/analyze_operating_drivers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker: data.value.ticker,
                company_name: data.value.company_name,
                sector: data.value.sector
            })
        });
        if (!response.ok) throw new Error('Failed to generate analysis');
        const result = await response.json();
        driversReport.value = result.report;
        await saveReport(`Operating Drivers: ${data.value.company_name}`, result.report, 'operating_drivers');
    } catch (e) {
        console.error(e);
        if (!analyzing.value) alert("Failed to generate drivers analysis");
        throw e;
    } finally {
        analyzingDrivers.value = false;
    }
};



const calculateRevenueGrowth = () => {
    if (!data.value || !data.value.financials || !data.value.financials.annual) return '-';
    try {
        const revenues = Object.values(data.value.financials.annual['Total Revenue'] || {});
        if (revenues.length < 2) return '-';
        const latest = revenues[0];
        const previous = revenues[1];
        if (!latest || !previous) return '-';
        const growth = ((latest - previous) / previous) * 100;
        return growth.toFixed(2);
    } catch {
        return '-';
    }
};

// Helper functions for financial statement tables
const getFinancialYears = (statementType, period = 'annual') => {
    if (!data.value) return [];
    
    let statement;
    if (statementType === 'income') statement = data.value.financials;
    else if (statementType === 'balance') statement = data.value.balance_sheet;
    else if (statementType === 'cashflow') statement = data.value.cashflow;
    
    if (!statement) return [];
    
    // Use annual or quarterly data based on period
    const dataSource = period === 'annual' ? statement.annual : statement.quarterly;
    if (!dataSource) return [];
    
    // Get periods from the first item's keys
    const firstItem = Object.values(dataSource)[0];
    if (!firstItem) return [];
    
    // Extract and sort periods
    const periods = Object.keys(firstItem)
        .map(key => {
            try {
                return new Date(key);
            } catch {
                return null;
            }
        })
        .filter(date => date !== null)
        .sort((a, b) => b - a); // Sort descending (newest first)
    
    return [...new Set(periods.map(d => d.getTime()))]; // Return timestamps, remove duplicates
};

const getFinancialItems = (statementType, period = 'annual') => {
    if (!data.value) return [];
    
    let statement;
    if (statementType === 'income') statement = data.value.financials;
    else if (statementType === 'balance') statement = data.value.balance_sheet;
    else if (statementType === 'cashflow') statement = data.value.cashflow;
    
    if (!statement) return [];
    
    const dataSource = period === 'annual' ? statement.annual : statement.quarterly;
    if (!dataSource) return [];
    
    return Object.keys(dataSource);
};

const getFinancialValue = (statementType, item, yearOrLtm) => {
    if (!data.value) return null;
    
    let statement;
    if (statementType === 'income') statement = data.value.financials;
    else if (statementType === 'balance') statement = data.value.balance_sheet;
    else if (statementType === 'cashflow') statement = data.value.cashflow;
    
    if (!statement) return null;
    
    // Handle LTM
    if (yearOrLtm === 'ltm') {
        return statement.ltm?.[item];
    }
    
    // Handle annual data (for backward compatibility)
    if (!statement.annual || !statement.annual[item]) return null;
    
    // Find the value for the given year
    const itemData = statement.annual[item];
    for (const [key, value] of Object.entries(itemData)) {
        try {
            const date = new Date(key);
            if (date.getFullYear() === yearOrLtm) {
                return value;
            }
        } catch {
            continue;
        }
    }
    
    return null;
};

const getFinancialValueByPeriod = (statementType, item, periodTimestamp, period = 'annual') => {
    if (!data.value) return null;
    
    let statement;
    if (statementType === 'income') statement = data.value.financials;
    else if (statementType === 'balance') statement = data.value.balance_sheet;
    else if (statementType === 'cashflow') statement = data.value.cashflow;
    
    if (!statement) return null;
    
    const dataSource = period === 'annual' ? statement.annual : statement.quarterly;
    if (!dataSource || !dataSource[item]) return null;
    
    // Find the value for the given period timestamp
    const itemData = dataSource[item];
    for (const [key, value] of Object.entries(itemData)) {
        try {
            const date = new Date(key);
            if (date.getTime() === periodTimestamp) {
                return value;
            }
        } catch {
            continue;
        }
    }
    
    return null;
};

const formatPeriodLabel = (timestamp) => {
    try {
        const date = new Date(timestamp);
        if (financialPeriod.value === 'annual') {
            return date.getFullYear().toString();
        } else {
            // Format as Q1 2024, Q2 2024, etc.
            const year = date.getFullYear();
            const month = date.getMonth();
            const quarter = Math.floor(month / 3) + 1;
            return `Q${quarter} ${year}`;
        }
    } catch {
        return timestamp;
    }
};

const formatFinancialNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    if (num === 0) return '0';
    
    const absNum = Math.abs(num);
    const sign = num < 0 ? '-' : '';
    
    if (absNum >= 1e9) return sign + (absNum / 1e9).toFixed(2) + 'B';
    if (absNum >= 1e6) return sign + (absNum / 1e6).toFixed(2) + 'M';
    if (absNum >= 1e3) return sign + (absNum / 1e3).toFixed(2) + 'K';
    return sign + absNum.toLocaleString(undefined, { maximumFractionDigits: 0 });
};

const getRevenueGrowthClass = () => {
    const growth = parseFloat(calculateRevenueGrowth());
    if (isNaN(growth)) return '';
    return growth >= 0 ? 'positive' : 'negative';
};

// Chart rendering functions
const renderFinancialCharts = () => {
    if (!data.value) return;
    
    // Destroy existing charts safely using Chart.getChart
    // This ensures we destroy the instance attached to the canvas even if our local reference is lost
    const charts = [
        { ref: revenueProfitChart, instance: revenueProfitChartInstance },
        { ref: cashflowChart, instance: cashflowChartInstance },
        { ref: assetsChart, instance: assetsChartInstance },
        { ref: liabilitiesChart, instance: liabilitiesChartInstance }
    ];

    charts.forEach(({ ref }) => {
        if (ref.value) {
            const chart = Chart.getChart(ref.value);
            if (chart) {
                chart.destroy();
            }
        }
    });
    
    // Reset local instances
    revenueProfitChartInstance = null;
    cashflowChartInstance = null;
    assetsChartInstance = null;
    liabilitiesChartInstance = null;
    
    renderRevenueProfitChart();
    renderCashflowChart();
    renderBalanceSheetCharts();
};

const renderRevenueProfitChart = () => {
    if (!revenueProfitChart.value) return;
    
    const periods = getFinancialYears('income', financialPeriod.value);
    
    // Build data arrays and filter out periods with null values
    const validData = [];
    for (const period of periods) {
        const revenue = getFinancialValueByPeriod('income', 'Total Revenue', period, financialPeriod.value);
        const netIncome = getFinancialValueByPeriod('income', 'Net Income', period, financialPeriod.value);
        
        // Only include if both revenue and net income have valid data
        if (revenue !== null && revenue !== undefined && netIncome !== null && netIncome !== undefined) {
            validData.push({
                period: period,
                label: formatPeriodLabel(period),
                revenue: revenue,
                netIncome: netIncome
            });
        }
    }
    
    // Reverse to show oldest to newest (left to right)
    validData.reverse();
    
    const labels = validData.map(d => d.label);
    const revenues = validData.map(d => d.revenue);
    const netIncomes = validData.map(d => d.netIncome);
    
    revenueProfitChartInstance = new Chart(revenueProfitChart.value, {
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
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#42b983',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#42b983',
                    pointHoverBorderWidth: 3
                },
                {
                    label: 'Net Income',
                    data: netIncomes,
                    borderColor: '#8e44ad',
                    backgroundColor: 'rgba(142, 68, 173, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#8e44ad',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#8e44ad',
                    pointHoverBorderWidth: 3
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
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 13,
                            weight: 'bold'
                        }
                    },
                    onClick: (e, legendItem, legend) => {
                        const index = legendItem.datasetIndex;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(index);
                        meta.hidden = !meta.hidden;
                        chart.update();
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#42b983',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: (context) => {
                            return context[0].label;
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = '$' + formatFinancialNumber(context.parsed.y);
                            return label + ': ' + value;
                        },
                        afterLabel: (context) => {
                            // Calculate percentage change from previous period
                            const datasetIndex = context.datasetIndex;
                            const dataIndex = context.dataIndex;
                            if (dataIndex > 0) {
                                const currentValue = context.parsed.y;
                                const previousValue = context.chart.data.datasets[datasetIndex].data[dataIndex - 1];
                                if (previousValue && currentValue) {
                                    const change = ((currentValue - previousValue) / previousValue * 100).toFixed(2);
                                    const arrow = change >= 0 ? '↑' : '↓';
                                    return `${arrow} ${Math.abs(change)}% vs prior period`;
                                }
                            }
                            return '';
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
                            size: 12,
                            weight: 'bold'
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: (value) => '$' + formatFinancialNumber(value),
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            hover: {
                mode: 'index',
                intersect: false
            }
        }
    });
};

const renderCashflowChart = () => {
    if (!cashflowChart.value) return;
    
    const periods = getFinancialYears('cashflow', financialPeriod.value);
    
    // Build data arrays and filter out periods with null values
    const validData = [];
    for (const period of periods) {
        const operating = getFinancialValueByPeriod('cashflow', 'Operating Cash Flow', period, financialPeriod.value);
        const investing = getFinancialValueByPeriod('cashflow', 'Investing Cash Flow', period, financialPeriod.value);
        const financing = getFinancialValueByPeriod('cashflow', 'Financing Cash Flow', period, financialPeriod.value);
        
        // Only include if at least operating cash flow has valid data
        if (operating !== null && operating !== undefined) {
            validData.push({
                period: period,
                label: formatPeriodLabel(period),
                operating: operating || 0,
                investing: investing || 0,
                financing: financing || 0
            });
        }
    }
    
    // Reverse to show oldest to newest (left to right)
    validData.reverse();
    
    const labels = validData.map(d => d.label);
    const operating = validData.map(d => d.operating);
    const investing = validData.map(d => d.investing);
    const financing = validData.map(d => d.financing);
    
    cashflowChartInstance = new Chart(cashflowChart.value, {
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
                            return context.dataset.label + ': $' + formatFinancialNumber(context.parsed.y);
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
    });
};

const renderBalanceSheetCharts = () => {
    if (!assetsChart.value || !liabilitiesChart.value) return;
    
    // Assets composition
    const currentAssets = getFinancialValue('balance', 'Current Assets', 'ltm') || 0;
    const totalAssets = getFinancialValue('balance', 'Total Assets', 'ltm') || 0;
    const nonCurrentAssets = totalAssets - currentAssets;
    
    assetsChartInstance = new Chart(assetsChart.value, {
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
                            return context.label + ': $' + formatFinancialNumber(context.parsed);
                        }
                    }
                }
            }
        }
    });
    
    // Liabilities & Equity composition
    const currentLiabilities = getFinancialValue('balance', 'Current Liabilities', 'ltm') || 0;
    const totalLiabilities = getFinancialValue('balance', 'Total Liabilities Net Minority Interest', 'ltm') || 0;
    const equity = getFinancialValue('balance', 'Stockholders Equity', 'ltm') || 0;
    const nonCurrentLiabilities = totalLiabilities - currentLiabilities;
    
    liabilitiesChartInstance = new Chart(liabilitiesChart.value, {
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
                            return context.label + ': $' + formatFinancialNumber(context.parsed);
                        }
                    }
                }
            }
        }
    });
};

// Helper function to prepare options data
const prepareOptionsData = () => {
    if (!data.value || !data.value.trading || !data.value.trading.options) return null;
    
    const options = data.value.trading.options;
    if (options.length === 0) return null;
    
    // Sort by expiration date
    const sortedOptions = [...options].sort((a, b) => {
        return new Date(a.expirationDate) - new Date(b.expirationDate);
    });
    
    const labels = sortedOptions.map(opt => {
        const date = new Date(opt.expirationDate);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    });
    
    return {
        labels,
        totalVolumes: sortedOptions.map(opt => opt.totalVolume),
        totalOpenInterests: sortedOptions.map(opt => opt.totalOpenInterest),
        callsVolumes: sortedOptions.map(opt => opt.callsVolume),
        putsVolumes: sortedOptions.map(opt => opt.putsVolume)
    };
};

const renderOptionsVolumeChart = () => {
    if (!optionsVolumeChart.value) return;
    
    const chartData = prepareOptionsData();
    if (!chartData) return;
    
    // Destroy existing chart safely
    const chart = Chart.getChart(optionsVolumeChart.value);
    if (chart) {
        chart.destroy();
    }
    
    optionsVolumeChartInstance = new Chart(optionsVolumeChart.value, {
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
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Total Open Interest',
                    data: chartData.totalOpenInterests,
                    borderColor: '#8e44ad',
                    backgroundColor: 'rgba(142, 68, 173, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
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
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    onClick: (e, legendItem, legend) => {
                        const index = legendItem.datasetIndex;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(index);
                        meta.hidden = !meta.hidden;
                        chart.update();
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#42b983',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: (context) => {
                            return context[0].label;
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = formatNumber(context.parsed.y);
                            return label + ': ' + value;
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
                            size: 11,
                            weight: 'bold'
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: (value) => formatNumber(value),
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            hover: {
                mode: 'index',
                intersect: false
            }
        }
    });
};

const renderOptionsCallsPutsChart = () => {
    if (!optionsCallsPutsChart.value) return;
    
    const chartData = prepareOptionsData();
    if (!chartData) return;
    
    // Destroy existing chart safely
    const chart = Chart.getChart(optionsCallsPutsChart.value);
    if (chart) {
        chart.destroy();
    }
    
    optionsCallsPutsChartInstance = new Chart(optionsCallsPutsChart.value, {
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
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Puts Volume',
                    data: chartData.putsVolumes,
                    borderColor: '#c0392b',
                    backgroundColor: 'rgba(192, 57, 43, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
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
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    onClick: (e, legendItem, legend) => {
                        const index = legendItem.datasetIndex;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(index);
                        meta.hidden = !meta.hidden;
                        chart.update();
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#42b983',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: (context) => {
                            return context[0].label;
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = formatNumber(context.parsed.y);
                            return label + ': ' + value;
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
                            size: 11,
                            weight: 'bold'
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: (value) => formatNumber(value),
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            hover: {
                mode: 'index',
                intersect: false
            }
        }
    });
};

// Filings sorting
const filingsSortBy = ref('date');
const filingsSortOrder = ref('desc'); // 'asc' or 'desc'

const sortedFilings = computed(() => {
    if (!data.value || !data.value.filings) return [];
    
    const filings = [...data.value.filings];
    
    return filings.sort((a, b) => {
        if (filingsSortBy.value === 'type') {
            // Sort alphabetically by type
            const comparison = a.type.localeCompare(b.type);
            return filingsSortOrder.value === 'asc' ? comparison : -comparison;
        } else if (filingsSortBy.value === 'date') {
            // Sort by date
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            const comparison = dateA - dateB;
            return filingsSortOrder.value === 'asc' ? comparison : -comparison;
        }
        return 0;
    });
});

const sortFilings = (column) => {
    if (filingsSortBy.value === column) {
        // Toggle sort order
        filingsSortOrder.value = filingsSortOrder.value === 'asc' ? 'desc' : 'asc';
    } else {
        // New column, default to desc for date, asc for type
        filingsSortBy.value = column;
        filingsSortOrder.value = column === 'date' ? 'desc' : 'asc';
    }
};

const getSortIcon = (column) => {
    if (filingsSortBy.value !== column) return '⇅';
    return filingsSortOrder.value === 'asc' ? '↑' : '↓';
};

const formatFilingDate = (dateStr) => {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    } catch {
        return dateStr;
    }
};

// Holders / Trade Log functions
const holdersView = ref('insider'); // 'all', 'institutions', 'insider'

const getInsiderTransactions = () => {
    if (!data.value || !data.value.holders || !data.value.holders.insider) return [];
    const insider = data.value.holders.insider;
    // Convert object to array
    return Object.values(insider).slice(0, 50); // Limit to 50 most recent
};

const getInstitutionalHolders = () => {
    if (!data.value || !data.value.holders || !data.value.holders.institutional) return [];
    const institutional = data.value.holders.institutional;
    
    // The data structure from df_to_dict is: {column_name: {row_index: value}}
    // Example: {'Date Reported': {0: timestamp, 1: timestamp}, 'Holder': {0: 'Vanguard', 1: 'Blackrock'}, ...}
    
    const columnNames = Object.keys(institutional);
    if (columnNames.length === 0) return [];
    
    // Get all row indices (0, 1, 2, ...) from the first column
    const firstColumn = institutional[columnNames[0]];
    if (!firstColumn || typeof firstColumn !== 'object') return [];
    
    const rowIndices = Object.keys(firstColumn).map(idx => parseInt(idx)).filter(idx => !isNaN(idx));
    if (rowIndices.length === 0) return [];
    
    // Build rows by combining all columns for each row index
    const holders = rowIndices.map(rowIdx => {
        const row = {};
        columnNames.forEach(col => {
            if (institutional[col] && institutional[col][rowIdx] !== undefined) {
                row[col] = institutional[col][rowIdx];
            }
        });
        return row;
    });
    
    // Sort by Date Reported descending (most recent first), then by Value descending
    holders.sort((a, b) => {
        const dateA = a['Date Reported'] ? new Date(a['Date Reported']) : new Date(0);
        const dateB = b['Date Reported'] ? new Date(b['Date Reported']) : new Date(0);
        if (dateB.getTime() !== dateA.getTime()) {
            return dateB - dateA;
        }
        // If dates are equal, sort by value descending
        const valueA = a.Value || 0;
        const valueB = b.Value || 0;
        return valueB - valueA;
    });
    
    return holders.slice(0, 50); // Limit to 50 most recent
};

const formatTradeDate = (dateStr) => {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        }).toUpperCase();
    } catch {
        return dateStr;
    }
};

const extractAction = (text) => {
    if (!text) return 'N/A';
    if (text.toLowerCase().includes('sale')) return 'SELL';
    if (text.toLowerCase().includes('purchase')) return 'PURCHASE';
    if (text.toLowerCase().includes('gift')) return 'STOCK GIFT';
    if (text.toLowerCase().includes('no change')) return 'NO CHANGE';
    if (text.toLowerCase().includes('option')) return 'OPTION EXERCISE';
    return 'OTHER';
};

const getActionClass = (text) => {
    const action = extractAction(text);
    if (action === 'SELL') return 'action-sell';
    if (action === 'PURCHASE') return 'action-purchase';
    return '';
};

const getChangeClass = (pctChange) => {
    if (!pctChange && pctChange !== 0) return '';
    if (pctChange > 0) return 'action-purchase';
    if (pctChange < 0) return 'action-sell';
    return '';
};

const formatPercentChange = (value) => {
    if (value === null || value === undefined) return '-';
    const sign = value >= 0 ? '+' : '';
    return sign + (value * 100).toFixed(2) + '%';
};

const renderMarkdown = (text) => {
    return marked(text);
};

const formatDate = (timestamp) => {
    try {
        return new Date(parseInt(timestamp) / 1000000).getFullYear();
    } catch {
        return timestamp;
    }
};

const formatNumber = (num) => {
    if (!num && num !== 0) return '-';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toLocaleString();
};

const formatPercent = (num) => {
    if (!num && num !== 0) return '-';
    // If already in percentage form (0-100)
    if (num > 1 || num < -1) return num.toFixed(2) + '%';
    // If in decimal form (0-1)
    return (num * 100).toFixed(2) + '%';
};

const formatRatio = (num) => {
    if (!num && num !== 0) return '-';
    return num.toFixed(2);
};

const formatDays = (num) => {
    if (!num && num !== 0) return '-';
    return num.toFixed(0) + ' days';
};
const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    const absVal = Math.abs(value);
    if (absVal >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B';
    if (absVal >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M';
    if (absVal >= 1e3) return '$' + (value / 1e3).toFixed(2) + 'K';
    return '$' + value.toFixed(2);
};

</script>

<style scoped>
.micro-view { padding: 20px 20px 50px 0; }
.search-bar { margin-bottom: 20px; display: flex; gap: 10px; }
.search-bar input { padding: 8px; font-size: 16px; width: 200px; }
.search-bar button { padding: 8px 16px; background: #42b983; color: white; border: none; cursor: pointer; }
.header { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
.price-info { font-size: 1.2em; color: #666; }
.price { font-weight: bold; color: #2c3e50; margin-right: 15px; }

.tabs { 
    display: flex; 
    gap: 5px; 
    margin-bottom: 20px; 
    border-bottom: 2px solid #ddd;
    flex-wrap: nowrap;
    overflow-x: auto;
    white-space: nowrap;
    scrollbar-width: none; /* Firefox */
}
.tabs::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera */
}

.tabs button {
    padding: 10px 15px;
    border: none;
    background: #f1f1f1;
    cursor: pointer;
    font-size: 0.9em;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
}

.tabs button::after {
    content: attr(data-text);
    height: 0;
    visibility: hidden;
    overflow: hidden;
    user-select: none;
    pointer-events: none;
    font-weight: bold;
}
.tabs button.active {
    background: #42b983;
    color: white;
    font-weight: bold;
}

.tab-pane { padding: 10px; }

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
.ai-btn:disabled { opacity: 0.7; cursor: wait; }

.progress-indicator {
    background: #e8f5e9;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
    font-weight: bold;
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

.ai-btn.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: #cccccc !important;
    color: #666666 !important;
}


.analysis-section {
    margin-bottom: 40px;
    padding-bottom: 30px;
    border-bottom: 2px solid #eee;
}

.analysis-section h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.report-content { background: #f9f9f9; padding: 20px; border-radius: 8px; line-height: 1.6; margin-bottom: 20px; }

.info-message {
    background: #fff3cd;
    padding: 15px;
    border-radius: 4px;
    color: #856404;
    margin-top: 10px;
}

/* Metrics Visualizations */
.metrics-viz, .capital-viz {
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
    color: #2c3e50;
}

.metric-trend {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 1.5em;
}

.metric-trend.positive { color: #42b983; }
.metric-trend.negative { color: #e74c3c; }

/* Bar Charts */
.efficiency-chart, .liquidity-section, .profitability-leverage {
    margin-top: 20px;
}

.efficiency-chart h5, .liquidity-section h5, .profitability-leverage h5 {
    margin-bottom: 15px;
    color: #2c3e50;
}

.leverage-bar {
    margin-bottom: 15px;
}

.bar-label {
    font-size: 0.9em;
    margin-bottom: 5px;
    color: #555;
}

.bar-container {
    background: #e0e0e0;
    height: 30px;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
}

.bar-fill {
    background: linear-gradient(90deg, #42b983, #2e7d32);
    height: 100%;
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 10px;
    color: white;
    font-weight: bold;
}

.bar-fill.liquidity {
    background: linear-gradient(90deg, #42b983, #66bb6a);
}

.bar-fill.debt {
    background: linear-gradient(90deg, #ff9800, #f57c00);
}

.bar-value {
    color: white;
    font-size: 0.85em;
    padding-right: 5px;
}

.bar-benchmark {
    font-size: 0.75em;
    color: #888;
    margin-top: 3px;
}

.comparison-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
}

.comparison-item {
    text-align: center;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
}

.comparison-label {
    font-size: 0.85em;
    color: #666;
    margin-bottom: 8px;
}

.comparison-value {
    font-size: 1.3em;
    font-weight: bold;
    color: #2c3e50;
}

.chart-bar {
    margin-bottom: 15px;
}

.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: right; white-space: nowrap; color: #2c3e50; }
th:first-child, td:first-child { 
    text-align: left; 
    font-weight: bold; 
    position: sticky; 
    left: 0; 
    background: white; 
    z-index: 2;
    min-width: 200px;
    max-width: 300px;
}
.item-name {
    font-size: 0.9em;
    color: #2c3e50;
}
th { 
    background: #f2f2f2; 
    position: sticky; 
    top: 0;
    z-index: 1;
    font-weight: bold;
}
.ltm-header {
    background: #d4edda !important;
    color: #155724;
    font-weight: bold;
}
.ltm-col { 
    background: #e8f5e9; 
    font-weight: bold;
    color: #2e7d32;
}
.no-data {
    padding: 40px;
    text-align: center;
    color: #999;
    font-style: italic;
}

.ratios-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.ratio-card { background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 8px; color: #2c3e50; }
.ratio-card h4 { margin-top: 0; color: #42b983; }
.ratio-card p { margin: 8px 0; }

/* Financial Statements Styles */
.financials-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.financials-header h3 {
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
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
}

.chart-section {
    flex: 1;
    background: white;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #ddd;
    min-width: 0; /* Prevent flex item from overflowing */
}

.chart-section h4 {
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
}

.composition-chart {
    flex: 1;
    min-width: 0;
    text-align: center;
}

.composition-chart h5 {
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

/* Filings Table Styles */
.filings-container {
    margin-top: 20px;
}

.filings-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

/* Trade Log Styles */
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
    color: #fff;
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
    background: #1a1a1a;
    color: #fff;
    border-radius: 8px;
    overflow: hidden;
}

.trade-log-table thead {
    background: #2c2c2c;
}

.trade-log-table th {
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    font-size: 0.85em;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: #2c2c2c; /* Override generic th background */
}


.trade-log-table tbody tr {
    border-bottom: 1px solid #2c2c2c;
    transition: background 0.2s;
}

.trade-log-table tbody tr:hover {
    background: #252525;
}

.trade-log-table tbody tr:last-child {
    border-bottom: none;
}

.trade-log-table td {
    padding: 12px 15px;
    font-size: 0.9em;
    background: #1a1a1a; /* Override generic td:first-child background */
    color: #fff; /* Ensure text is white */
}

.trade-log-table tbody tr:hover td {
    background: #252525; /* Ensure hover state works */
}

.trade-date {
    color: #ccc;
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
    color: #999;
    font-size: 0.85em;
}

.trade-insider {
    color: #fff;
    font-weight: 500;
}

.institutional-holders {
    margin-top: 20px;
}

.institutional-holders h4 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.loading, .error { margin-top: 20px; font-size: 1.2em; }
.error { color: #e74c3c; }

/* Options Trading Styles */
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

.options-chart-section h3 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #2c3e50;
}

.options-chart-section .chart-container {
    height: 400px;
    position: relative;
}
</style>
