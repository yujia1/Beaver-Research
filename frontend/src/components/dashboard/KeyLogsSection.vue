<template>
  <div class="key-logs-container">
        <div class="key-logs-section">
            <div class="key-logs-header">
                <h2>{{ t('dashboard.key_logs') }}</h2>
            </div>

            <!-- Tab Selector -->
            <div class="tab-selector">
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'equity' }"
                    @click="activeTab = 'equity'"
                >
                    {{ t('dashboard.tabs.equity') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'bond' }"
                    @click="activeTab = 'bond'"
                >
                    {{ t('dashboard.tabs.bond') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'economic' }"
                    @click="activeTab = 'economic'"
                >
                    {{ t('dashboard.tabs.economic') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'currency' }"
                    @click="activeTab = 'currency'"
                >
                    {{ t('dashboard.tabs.currency') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'commodity' }"
                    @click="activeTab = 'commodity'"
                >
                    {{ t('dashboard.tabs.commodity') }}
                </button>

                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'crypto' }"
                    @click="activeTab = 'crypto'"
                >
                    {{ t('dashboard.tabs.crypto') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'calendar' }"
                    @click="activeTab = 'calendar'"
                >
                    {{ t('dashboard.tabs.calendar') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'policy' }"
                    @click="activeTab = 'policy'"
                >
                    {{ t('dashboard.tabs.policy') }}
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'fed' }"
                    @click="activeTab = 'fed'"
                >
                    {{ t('dashboard.tabs.fed') }}
                </button>
            </div>

            <!-- Equity Tab Content -->
            <div v-if="activeTab === 'equity'" class="tab-content">
        <!-- Index Charts Section -->
                <div class="category-tabs">
                    <button 
                        :class="{ active: activeEquityCategory === 'indices' }"
                        @click="activeEquityCategory = 'indices'"
                    >
                        {{ t('dashboard.access_equity') || 'Indices' }}
                    </button>
                    <button 
                        :class="{ active: activeEquityCategory === 'market' }"
                        @click="activeEquityCategory = 'market'"
                    >
                        {{ t('dashboard.market') || 'Market' }}
                    </button>
                    <button 
                        :class="{ active: activeEquityCategory === 'most-actives' }"
                        @click="activeEquityCategory = 'most-actives'"
                    >
                        {{ t('dashboard.market_movers.most_actives') || 'Top Trade' }}
                    </button>
                    <button 
                        :class="{ active: activeEquityCategory === 'gainers' }"
                        @click="activeEquityCategory = 'gainers'"
                    >
                        {{ t('dashboard.market_movers.top_gainers') || 'Top Gainers' }}
                    </button>
                    <button 
                        :class="{ active: activeEquityCategory === 'losers' }"
                        @click="activeEquityCategory = 'losers'"
                    >
                        {{ t('dashboard.market_movers.top_losers') || 'Top Losers' }}
                    </button>
                </div>

                <IndicesSection v-if="activeEquityCategory === 'indices'" ref="indicesRef" />
                <MarketAnalysis v-if="activeEquityCategory === 'market'" />
                <MarketMovers v-if="activeEquityCategory === 'most-actives'" moverType="most-actives" />
                <MarketMovers v-if="activeEquityCategory === 'gainers'" moverType="gainers" />
                <MarketMovers v-if="activeEquityCategory === 'losers'" moverType="losers" />
                
                <!-- Market News Stream -->
                <MarketNews />

            </div>

            <!-- Bond Tab Content -->
            <div v-if="activeTab === 'bond'" class="tab-content bond-tab-content">
                <BondMarketSection ref="bondRef" />
            </div>

            <!-- Economic Tab Content -->
            <div v-if="activeTab === 'economic'" class="tab-content economic-tab-content">
                <div v-if="economicLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>{{ t('dashboard.loading_states.economic') }}</p>
                </div>
                <div v-else-if="economicError" class="error-state">
                    <p class="error-message">{{ economicError }}</p>
                </div>
                <div v-else class="economic-list-container">
                    <div 
                        v-for="(item, index) in economicIndicators.filter(item => item.series_id !== 'FEDWATCH')" 
                        :key="item.series_id" 
                        class="economic-item"
                        :class="{ expanded: expandedEconomicItems.has(index) }"
                    >
                        <!-- Indicator Header (Clickable) -->
                        <div class="economic-header" @click="toggleEconomicItem(index)">
                            <div class="header-left">
                                <span class="expand-icon">{{ expandedEconomicItems.has(index) ? '▼' : '▶' }}</span>
                                <h3 class="indicator-name">{{ item.indicator }}</h3>
                                <span class="category-badge" :class="`category-${item.category.toLowerCase()}`">
                                    {{ item.category }}
                                </span>
                            </div>
                            <div class="header-right">
                                <span class="current-value">{{ formatEconomicValue(item.value) }}</span>
                            </div>
                        </div>

                        <!-- Expandable Details Table -->
                        <div v-if="expandedEconomicItems.has(index)" class="economic-details">
                            <table class="details-table">
                                <tbody>
                                    <tr>
                                        <td class="label-cell">Indicator Name</td>
                                        <td class="value-cell">{{ item.indicator }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Description</td>
                                        <td class="value-cell">{{ item.description }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Current Value</td>
                                        <td class="value-cell">{{ formatEconomicValue(item.value) }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Last Updated</td>
                                        <td class="value-cell">{{ item.date }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Release Frequency</td>
                                        <td class="value-cell">{{ getEconomicFrequency(item.series_id) }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Next Release (Est.)</td>
                                        <td class="value-cell">{{ getNextReleaseDate(item.series_id, item.date) }}</td>
                                    </tr>
                                    <tr>
                                        <td class="label-cell">Data Source</td>
                                        <td class="value-cell">{{ getEconomicSource(item.series_id) }}</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <!-- Recent History -->
                            <div v-if="item.history && item.history.length > 0" class="history-section">
                                <h4>Recent History (Last 10 Releases)</h4>
                                <table class="history-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Value</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="(h, hIndex) in getRecentHistory(item.history)" :key="hIndex">
                                            <td>{{ h.date }}</td>
                                            <td>{{ formatEconomicValue(h.value) }}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Fed Tab Content -->
            <div v-if="activeTab === 'fed'" class="tab-content fed-tab-content">
                <div class="category-tabs">
                    <button 
                        :class="{ active: activeFedCategory === 'liquidity' }"
                        @click="activeFedCategory = 'liquidity'"
                    >
                        {{ t('dashboard.categories.liquidity') }}
                    </button>
                    <button 
                        :class="{ active: activeFedCategory === 'forecasting' }"
                        @click="activeFedCategory = 'forecasting'"
                    >
                        {{ t('dashboard.categories.forecasting') }}
                    </button>
                </div>

                <div v-if="fedLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>{{ t('dashboard.loading_states.fed') }}</p>
                </div>
                <div v-else-if="fedError" class="error-state">
                    <p class="error-message">{{ fedError }}</p>
                </div>
                <div v-else class="fed-data">
                    <!-- Liquidity Section -->
                    <div v-if="activeFedCategory === 'liquidity'" class="category-section">
                        <!-- Balance Sheet / QT -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.balance_sheet') }}</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>{{ t('dashboard.headers.indicators') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                    </tr>
                </thead>
                <tbody>
                                    <tr>
                                        <td>WALCL</td>
                                        <td>Fed Total Assets</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/WALCL" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/WALCL</a></td>
                                    </tr>
                                    <tr>
                                        <td>WUTGAL</td>
                                        <td>Treasury Holdings</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/WUTGAL" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/WUTGAL</a></td>
                                    </tr>
                                    <tr>
                                        <td>WSHOMCB</td>
                                        <td>MBS Holdings</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/WSHOMCB" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/WSHOMCB</a></td>
                                    </tr>
                                    <tr>
                                        <td>H41</td>
                                        <td>H.4.1 Release</td>
                                        <td>liquidity</td>
                                        <td><a href="https://www.federalreserve.gov/releases/h41/" target="_blank" rel="noopener noreferrer">https://www.federalreserve.gov/releases/h41/</a></td>
                    </tr>
                </tbody>
            </table>
        </div>

                        <!-- Money Market Plumbing -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.money_market') }}</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>{{ t('dashboard.headers.indicators') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                    </tr>
                </thead>
                <tbody>
                                    <tr>
                                        <td>RRPONTSYD</td>
                                        <td>Reverse Repo Usage</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/RRPONTSYD" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/RRPONTSYD</a></td>
                                    </tr>
                                    <tr>
                                        <td>WRESBAL</td>
                                        <td>Reserve Balances</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/WRESBAL" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/WRESBAL</a></td>
                                    </tr>
                                    <tr>
                                        <td>IORB</td>
                                        <td>Interest on Reserve Balances</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/IORB" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/IORB</a></td>
                                    </tr>
                                    <tr>
                                        <td>SOFR</td>
                                        <td>SOFR</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/SOFR" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/SOFR</a></td>
                                    </tr>
                                    <tr>
                                        <td>EFFR</td>
                                        <td>Effective Fed Funds Rate</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/EFFR" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/EFFR</a></td>
                    </tr>
                </tbody>
            </table>
        </div>

                        <!-- Stress / Funding -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.stress_funding') }}</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>{{ t('dashboard.headers.indicators') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                    </tr>
                </thead>
                <tbody>
                                    <tr>
                                        <td>TEDRATE</td>
                                        <td>TED Spread</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/TEDRATE" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/TEDRATE</a></td>
                                    </tr>
                                    <tr>
                                        <td>STLFSI4</td>
                                        <td>Financial Stress Index</td>
                                        <td>liquidity</td>
                                        <td><a href="https://fred.stlouisfed.org/series/STLFSI4" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/STLFSI4</a></td>
                    </tr>
                </tbody>
            </table>
                        </div>
        </div>

                    <!-- Forecasting Section -->
                    <div v-if="activeFedCategory === 'forecasting'" class="category-section">
                        <!-- Yield Curve (Market-Implied Rate Path) -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.yield_curve') }}</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>{{ t('dashboard.headers.indicators') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                    </tr>
                </thead>
                <tbody>
                                    <tr>
                                        <td>DGS3MO</td>
                                        <td>3-Month Treasury Yield</td>
                                        <td>rate_path</td>
                                        <td><a href="https://fred.stlouisfed.org/series/DGS3MO" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/DGS3MO</a></td>
                                    </tr>
                                    <tr>
                                        <td>DGS2</td>
                                        <td>2-Year Treasury Yield</td>
                                        <td>rate_path</td>
                                        <td><a href="https://fred.stlouisfed.org/series/DGS2" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/DGS2</a></td>
                                    </tr>
                                    <tr>
                                        <td>DGS10</td>
                                        <td>10-Year Treasury Yield</td>
                                        <td>rate_path</td>
                                        <td><a href="https://fred.stlouisfed.org/series/DGS10" target="_blank" rel="noopener noreferrer">https://fred.stlouisfed.org/series/DGS10</a></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- Fed Policy / Forward Guidance -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.fed_policy') }}</h4>
                            <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>{{ t('dashboard.headers.indicators') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>FOMC_CALENDAR</td>
                                        <td>FOMC Calendar</td>
                                        <td>rate_path</td>
                                        <td><a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm" target="_blank" rel="noopener noreferrer">https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm</a></td>
                                    </tr>
                                    <tr>
                                        <td>MONETARY_POLICY</td>
                                        <td>Monetary Policy Overview</td>
                                        <td>rate_path</td>
                                        <td><a href="https://www.federalreserve.gov/monetarypolicy.htm" target="_blank" rel="noopener noreferrer">https://www.federalreserve.gov/monetarypolicy.htm</a></td>
                                    </tr>
                                    <tr>
                                        <td>H15</td>
                                        <td>H.15 Interest Rates Release</td>
                                        <td>rate_path</td>
                                        <td><a href="https://www.federalreserve.gov/releases/h15/" target="_blank" rel="noopener noreferrer">https://www.federalreserve.gov/releases/h15/</a></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- FedWatch Tool Graph -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">{{ t('dashboard.categories.fed_watch') }}</h4>
                            <div class="indicators">
                                <div v-for="item in fedIndicators" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Bar v-if="item.chart_type === 'bar'" :data="getFedChartData(item)" :options="barChartOptions" />
                                        <Line v-else :data="getFedChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Currency Tab Content -->
            <div v-if="activeTab === 'currency'" class="tab-content currency-tab-content">
                <div class="currency-data">
                    <div v-if="currencyLoading" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>{{ t('dashboard.loading_states.currency') }}</p>
                    </div>
                    <div v-else-if="currencyError" class="error-state">
                        <p class="error-message">{{ currencyError }}</p>
                    </div>
                    <div v-else class="indicators">
                        <div v-for="item in currencyIndicators" :key="item.symbol" class="indicator-card">
                            <div class="card-content">
                                <h3>{{ item.name }}</h3>
                                <p class="value">{{ item.value ? item.value.toFixed(4) : 'N/A' }}</p>
                                <p class="date">{{ item.date }}</p>
                                <p class="desc">
                                    {{ item.description || '&nbsp;' }}
                                    <span v-if="getCurrencyDailyChange(item)" :class="getCurrencyDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                        {{ getCurrencyDailyChange(item) >= 0 ? '+' : '' }}{{ getCurrencyDailyChange(item).toFixed(2) }}%
                                    </span>
                                </p>
                                
                                <!-- Per-graph Timeframe Selector -->
                                <div class="card-timeframe-selector">
                                    <button 
                                        v-for="tf in currencyTimeframes" 
                                        :key="tf.value" 
                                        :class="{ active: item.selectedTimeframe === tf.value }"
                                        @click="updateCurrencyIndicatorTimeframe(item, tf.value)"
                                        :disabled="item.loading"
                                    >
                                        {{ tf.label }}
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Interactive Chart.js Chart -->
                            <div class="chart-container" v-if="item.history && item.history.length > 0">
                                <div v-if="item.loading" class="chart-loading-overlay">
                                    <div class="spinner-small"></div>
                                </div>
                                <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                            </div>
                            <div v-else class="no-data">
                                <p>{{ t('dashboard.no_data') }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Commodity Tab Content -->
            <div v-if="activeTab === 'commodity'" class="tab-content commodity-tab-content">
                <div class="category-tabs">
                    <button 
                        :class="{ active: activeCommodityCategory === 'financials' }"
                        @click="activeCommodityCategory = 'financials'"
                    >
                        {{ t('dashboard.categories.financials') || 'Financials' }}
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'metals' }"
                        @click="activeCommodityCategory = 'metals'"
                    >
                        {{ t('dashboard.categories.metals') }}
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'energy' }"
                        @click="activeCommodityCategory = 'energy'"
                    >
                        {{ t('dashboard.categories.energy') }}
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'agriculture' }"
                        @click="activeCommodityCategory = 'agriculture'"
                    >
                        {{ t('dashboard.categories.agriculture') || 'Agriculture' }}
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'softs_livestock' }"
                        @click="activeCommodityCategory = 'softs_livestock'"
                    >
                        {{ t('dashboard.categories.softs_livestock') || 'Softs & Livestock' }}
                    </button>
                </div>

                <div class="commodity-data">
                    <div v-if="commodityLoading" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>{{ t('dashboard.loading_states.commodity') }}</p>
                    </div>
                    <div v-else-if="commodityError" class="error-state">
                        <p class="error-message">{{ commodityError }}</p>
                    </div>
                    <div v-else>
                        <!-- Financials Section -->
                        <div v-if="activeCommodityCategory === 'financials'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.financials" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCommodityDailyChange(item)" :class="getCommodityDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCommodityDailyChange(item) >= 0 ? '+' : '' }}{{ getCommodityDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in commodityTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: item.selectedTimeframe === tf.value }"
                                                @click="updateCommodityIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Metals Section -->
                        <div v-if="activeCommodityCategory === 'metals'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.metals" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCommodityDailyChange(item)" :class="getCommodityDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCommodityDailyChange(item) >= 0 ? '+' : '' }}{{ getCommodityDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in commodityTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: item.selectedTimeframe === tf.value }"
                                                @click="updateCommodityIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Agricultural (Renamed to Agriculture) Section -->
                        <div v-if="activeCommodityCategory === 'agriculture'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.agriculture" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCommodityDailyChange(item)" :class="getCommodityDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCommodityDailyChange(item) >= 0 ? '+' : '' }}{{ getCommodityDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in commodityTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: item.selectedTimeframe === tf.value }"
                                                @click="updateCommodityIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Energy Section -->
                        <div v-if="activeCommodityCategory === 'energy'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.energy" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCommodityDailyChange(item)" :class="getCommodityDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCommodityDailyChange(item) >= 0 ? '+' : '' }}{{ getCommodityDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in commodityTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: item.selectedTimeframe === tf.value }"
                                                @click="updateCommodityIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Softs & Livestock Section -->
                        <div v-if="activeCommodityCategory === 'softs_livestock'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.softs_livestock" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCommodityDailyChange(item)" :class="getCommodityDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCommodityDailyChange(item) >= 0 ? '+' : '' }}{{ getCommodityDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in commodityTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: item.selectedTimeframe === tf.value }"
                                                @click="updateCommodityIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getEconomicChartData(item)" :options="economicChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Policy Tab Content -->
            <div v-if="activeTab === 'policy'" class="tab-content policy-tab-content">
                <!-- White House Policy Sources -->
                <div class="liquidity-subsection">
                    <h4 class="subsection-title">{{ t('dashboard.categories.white_house') }}</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>{{ t('dashboard.headers.resource') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                    </tr>
                                </thead>
                        <tbody>
                            <tr>
                                <td>White house briefings</td>
                                <td>White House Statements & Releases</td>
                                <td><a href="https://www.whitehouse.gov/briefing-room/statements-releases/" target="_blank" rel="noopener noreferrer">https://www.whitehouse.gov/briefing-room/statements-releases/</a></td>
                                <td>policy/federal/whitehouse_statements</td>
                            </tr>
                            <tr>
                                <td>White house fact sheets</td>
                                <td>White House Fact Sheets</td>
                                <td><a href="https://www.whitehouse.gov/fact-sheets/" target="_blank" rel="noopener noreferrer">https://www.whitehouse.gov/briefing-room/statements-releases/fact-sheets/</a></td>
                                <td>policy/federal/whitehouse_fact_sheets</td>
                            </tr>
                            <tr>
                                <td>Whitehouse executive orders</td>
                                <td>Executive Orders</td>
                                <td><a href="https://www.whitehouse.gov/presidential-actions/executive-orders/" target="_blank" rel="noopener noreferrer">https://www.whitehouse.gov/briefing-room/presidential-actions/executive-orders/</a></td>
                                <td>policy/federal/executive_orders</td>
                    </tr>
                </tbody>
            </table>
        </div>

                <!-- Federal Register -->
                <div class="liquidity-subsection">
                    <h4 class="subsection-title">{{ t('dashboard.categories.federal_register') }}</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>{{ t('dashboard.headers.resource') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                    </tr>
                                </thead>
                        <tbody>
                            <tr>
                                <td>Federal register</td>
                                <td>Federal Register – Rules, Notices, Proposals</td>
                                <td><a href="https://www.federalregister.gov/" target="_blank" rel="noopener noreferrer">https://www.federalregister.gov/</a></td>
                                <td>policy/federal/regulations_register</td>
                            </tr>
                            <tr>
                                <td>Federal register presidential</td>
                                <td>Presidential Documents (EOs, Memos, Orders)</td>
                                <td><a href="https://www.federalregister.gov/presidential-documents" target="_blank" rel="noopener noreferrer">https://www.federalregister.gov/presidential-documents</a></td>
                                <td>policy/federal/presidential_documents</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Congress Policy Sources -->
                <div class="liquidity-subsection">
                    <h4 class="subsection-title">{{ t('dashboard.categories.congress') }}</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>{{ t('dashboard.headers.resource') }}</th>
                                        <th>{{ t('dashboard.headers.name') }}</th>
                                        <th>{{ t('dashboard.headers.url') }}</th>
                                        <th>{{ t('dashboard.headers.type') }}</th>
                                    </tr>
                                </thead>
                        <tbody>
                            <tr>
                                <td>Congress legislation</td>
                                <td>Congress.gov – All Legislation</td>
                                <td><a href="https://www.congress.gov/legislation" target="_blank" rel="noopener noreferrer">https://www.congress.gov/legislation</a></td>
                                <td>policy/federal/legislation</td>
                            </tr>
                            <tr>
                                <td>Congress subjects</td>
                                <td>Congress.gov – Policy Topics</td>
                                <td><a href="https://www.congress.gov/subjects" target="_blank" rel="noopener noreferrer">https://www.congress.gov/subjects</a></td>
                                <td>policy/federal/legislation_topics</td>
                            </tr>
                        </tbody>
                    </table>
    </div>
    </div>

            <!-- Calendar Tab Content -->
            <div v-if="activeTab === 'calendar'" class="tab-content calendar-tab-content">
                <div v-if="calendarLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Economic Calendar...</p>
                </div>
                <div v-else-if="calendarError" class="error-state">
                    <p class="error-message">{{ calendarError }}</p>
                </div>
                <div v-else class="calendar-data">
                    <div class="calendar-filters">
                        <div class="filter-group">
                            <span class="filter-label">Impact:</span>
                            <div class="custom-dropdown" :class="{ open: showImpactDropdown }">
                                <button class="dropdown-toggle" @click="showImpactDropdown = !showImpactDropdown">
                                    {{ selectedImpacts.length > 0 ? (selectedImpacts.length <= 2 ? selectedImpacts.join(', ') : selectedImpacts.length + ' Selected') : 'Select Impact' }}
                                    <span class="chevron">▼</span>
                                </button>
                                <div class="dropdown-menu" v-if="showImpactDropdown">
                                    <div 
                                        v-for="impact in calendarImpacts" :key="impact" 
                                        class="dropdown-item" 
                                        @click="toggleImpact(impact)"
                                        :class="{ selected: selectedImpacts.includes(impact) }"
                                    >
                                        <span class="check-box">{{ selectedImpacts.includes(impact) ? '☑' : '☐' }}</span>
                                        {{ impact }}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="filter-group">
                            <span class="filter-label">Country:</span>
                             <div class="custom-dropdown" :class="{ open: showCountryDropdown }">
                                <button class="dropdown-toggle" @click="showCountryDropdown = !showCountryDropdown">
                                    {{ selectedCountries.length > 0 ? selectedCountries.length + ' Selected' : 'Select Country' }}
                                    <span class="chevron">▼</span>
                                </button>
                                <div class="dropdown-menu" v-if="showCountryDropdown">
                                    <div 
                                        v-for="country in calendarCountries" :key="country" 
                                        class="dropdown-item" 
                                        @click="toggleCountry(country)"
                                        :class="{ selected: selectedCountries.includes(country) }"
                                    >
                                        <span class="check-box">{{ selectedCountries.includes(country) ? '☑' : '☐' }}</span>
                                        {{ country }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <table class="liquidity-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Country</th>
                                <th>Event</th>
                                <th>Actual</th>
                                <th>Previous</th>
                                <th>Estimate</th>
                                <th>Impact</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(item, index) in filteredCalendarData" :key="index">
                                <td>{{ item.date }}</td>
                                <td>{{ item.country }}</td>
                                <td>{{ item.event }}</td>
                                <td>{{ item.actual !== null ? item.actual : '-' }}</td>
                                <td>{{ item.previous !== null ? item.previous : '-' }}</td>
                                <td>{{ item.estimate !== null ? item.estimate : '-' }}</td>
                                <td>{{ item.impact }}</td>
                            </tr>
                            <tr v-if="filteredCalendarData.length === 0">
                                <td colspan="7" class="no-data">No events match filters.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Crypto Tab Content -->
            <div v-if="activeTab === 'crypto'" class="tab-content crypto-tab-content">
                <div class="crypto-data">
                    <div v-if="cryptoLoading" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>Loading Crypto Data...</p>
                    </div>
                    <div v-else-if="cryptoError" class="error-state">
                        <p class="error-message">{{ cryptoError }}</p>
                    </div>
                    <div v-else>
                        <div class="category-section">
                            <div class="indicators">
                                <div v-for="item in cryptoIndicators" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.price ? item.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">
                                            {{ item.description || '&nbsp;' }}
                                            <span v-if="getCryptoDailyChange(item)" :class="getCryptoDailyChange(item) >= 0 ? 'positive' : 'negative'" class="daily-change">
                                                {{ getCryptoDailyChange(item) >= 0 ? '+' : '' }}{{ getCryptoDailyChange(item).toFixed(2) }}%
                                            </span>
                                        </p>
                                        
                                        <!-- Per-graph Timeframe Selector -->
                                        <div class="card-timeframe-selector">
                                            <button 
                                                v-for="tf in cryptoTimeframes" 
                                                :key="tf.value" 
                                                :class="{ active: (item.selectedTimeframe || 'daily') === tf.value }"
                                                @click="updateCryptoIndicatorTimeframe(item, tf.value)"
                                                :disabled="item.loading"
                                            >
                                                {{ tf.label }}
                                            </button>
        </div>
    </div>
                                    
                                    <!-- Interactive Chart.js Chart -->
                                    <div class="chart-container" v-if="item.history && item.history.length > 0">
                                        <div v-if="item.loading" class="chart-loading-overlay">
                                            <div class="spinner-small"></div>
                                        </div>
                                        <Line :data="getCryptoChartData(item)" :options="cryptoChartOptions" />
                                    </div>
                                    <div v-else class="no-data">
                                        <p>{{ t('dashboard.no_data') }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>


        </div>
    </div>
</template>

<script setup>
import MarketAnalysis from './MarketAnalysis.vue'
import MarketMovers from './MarketMovers.vue'
import MarketNews from './MarketNews.vue'
import API_BASE_URL from '@/config/api.js'

import { ref, onMounted, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import IndicesSection from './IndicesSection.vue';
import BondMarketSection from './BondMarketSection.vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar, Doughnut, Pie } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../../utils/dailyCache.js'

const { t } = useI18n();

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

const loading = ref(false);
const activeTab = ref('equity');
const activeEquityCategory = ref('indices');
const indicesRef = ref(null);
const bondRef = ref(null);

// Bond Tab State
// Bond state managed in BondMarketSection

// Economic Tab State (from MacroView)
const economicIndicators = ref([]);
const economicLoading = ref(false);
const economicError = ref(null);
const economicTimeframes = computed(() => [
    { label: t('dashboard.timeframes.monthly'), value: 'monthly' },
    { label: t('dashboard.timeframes.quarterly'), value: 'quarterly' },
    { label: t('dashboard.timeframes.yearly'), value: 'yearly' },
    { label: t('dashboard.timeframes.5y'), value: '5y' }
]);

// Expandable economic items state
const expandedEconomicItems = ref(new Set());

// Fed Tab State
const fedIndicators = ref([]);
const fedLoading = ref(false);
const fedError = ref(null);
const activeFedCategory = ref('forecasting');
const fedTimeframes = computed(() => [
    { label: t('dashboard.timeframes.monthly'), value: 'monthly' },
    { label: t('dashboard.timeframes.quarterly'), value: 'quarterly' },
    { label: t('dashboard.timeframes.yearly'), value: 'yearly' },
    { label: t('dashboard.timeframes.5y'), value: '5y' }
]);

// Currency Tab State
const currencyIndicators = ref([]);
const currencyLoading = ref(false);
const currencyError = ref(null);
const currencyTimeframes = computed(() => [
  { label: t('dashboard.timeframes.monthly'), value: 'monthly' },
  { label: t('dashboard.timeframes.quarterly'), value: 'quarterly' },
  { label: t('dashboard.timeframes.yearly'), value: 'yearly' },
  { label: t('dashboard.timeframes.5y'), value: '5y' }
]);

// Commodity Tab State
const activeCommodityCategory = ref('financials');
const commodityIndicators = ref({
  financials: [],
  metals: [],
  energy: [],
  agriculture: [],
  softs_livestock: []
});
const commodityLoading = ref(false);
const commodityError = ref(null);
const commodityTimeframes = computed(() => [
  { label: t('dashboard.timeframes.monthly'), value: 'monthly' },
  { label: t('dashboard.timeframes.quarterly'), value: 'quarterly' },
  { label: t('dashboard.timeframes.yearly'), value: 'yearly' },
  { label: t('dashboard.timeframes.5y'), value: '5y' }
]);

// Crypto Tab State
const cryptoIndicators = ref([]);
const cryptoLoading = ref(false);
const cryptoError = ref(null);
const cryptoTimeframes = computed(() => [
  { label: t('dashboard.timeframes.daily'), value: 'daily' },
  { label: t('dashboard.timeframes.weekly'), value: 'weekly' },
  { label: t('dashboard.timeframes.monthly'), value: 'monthly' },
  { label: t('dashboard.timeframes.yearly'), value: 'yearly' }
]);

// Bond cache configuration
const BOND_CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const BOND_CACHE_KEY_PREFIX = 'bond_series_';

const getBondCacheKey = (seriesId, timeframe) => `${BOND_CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

// Economic cache configuration
const ECONOMIC_CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const ECONOMIC_CACHE_KEY_PREFIX = 'macro_series_';

const getEconomicCacheKey = (seriesId, timeframe) => `${ECONOMIC_CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

const getEconomicCachedData = (seriesId, timeframe) => {
    try {
        const key = getEconomicCacheKey(seriesId, timeframe);
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < ECONOMIC_CACHE_EXPIRATION) {
            return data;
        }
        localStorage.removeItem(key);
        return null;
    } catch (e) {
        return null;
    }
};

const setEconomicCachedData = (seriesId, timeframe, data) => {
    try {
        const key = getEconomicCacheKey(seriesId, timeframe);
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.error('Cache write error', e);
    }
};











const priceTimeframes = [
    { label: 'Days', value: 'days' },
    { label: 'Weekly', value: 'weekly' },
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: '5 Years', value: '5y' }
];



// Market indices data
// Indices state managed in IndicesSection

// Indices logic managed in IndicesSection

const updateCommodityData = async () => {
    clearCacheByKey('commodity_data_monthly');
    await fetchCommodityData();
};

const updateCurrencyData = async () => {
  clearCacheByKey('currency_data_monthly');
  await fetchCurrencyData();
};

const updateCryptoData = async () => {
  clearCacheByKey('crypto_data_daily');
  await fetchCryptoData();
};

const clearAllTimeframeCaches = () => {
    // Clear all bond series timeframe caches
    try {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(BOND_CACHE_KEY_PREFIX) || key.startsWith(ECONOMIC_CACHE_KEY_PREFIX)) {
                localStorage.removeItem(key);
            }
        });
    } catch (e) {
        console.error('Error clearing timeframe caches:', e);
    }
};

const loadTabContent = async (tab) => {
    switch (tab) {
        case 'equity':
            // Equity sub-tabs are handled by v-if components which fetch on mount
            if (activeEquityCategory.value === 'indices' && indicesRef.value) {
                // indicesRef might not be ready on first tick if v-if just became true
                // But indices component fetches on mount anyway.
            }
            break;
        case 'bond':
            // Bond component fetches on mount
            if (bondRef.value) {
                // bondRef.value.refresh(); // No need, it fetches on mount
            }
            break;
        case 'economic':
            if (economicIndicators.value.length === 0) await fetchEconomicData();
            break;
        case 'fed':
            if (fedIndicators.value.length === 0) await fetchFedData();
            break;
        case 'currency':
            if (currencyIndicators.value.length === 0) await fetchCurrencyData();
            break;
        case 'commodity':
            if (Object.keys(commodityIndicators.value).length === 0) await fetchCommodityData();
            break;
        case 'crypto':
            if (cryptoIndicators.value.length === 0) await fetchCryptoData();
            break;
        case 'policy':
             // Policy content is static/links, no fetch needed
            break;
        case 'calendar':
            if (calendarData.value.length === 0) await fetchCalendarData();
            break;
    }
};

const updateData = async () => {
    // smart refresh: only refresh the active tab
    loading.value = true;
    
    try {
        switch (activeTab.value) {
            case 'equity':
                if (activeEquityCategory.value === 'indices' && indicesRef.value) {
                    await indicesRef.value.refresh();
                }
                // Other equity categories (Market, Top Movers) are robust enough to re-mount or we could add refresh methods
                // For now, indices is the main one with explicit refresh
                break;
            case 'bond':
                if (bondRef.value) await bondRef.value.refresh();
                break;
            case 'economic':
                await updateEconomicData();
                break;
            case 'fed':
                await updateFedData();
                break;
            case 'currency':
                // Custom update logic for currency (clear cache and fetch)
                clearCacheByKey('currency_data_monthly');
                currencyIndicators.value = []; // Clear current to force update
                await fetchCurrencyData();
                break;
            case 'commodity':
                // Custom update logic for commodity
                clearCacheByKey('commodity_data_monthly');
                commodityIndicators.value = {};
                await fetchCommodityData();
                break;
            case 'crypto':
                // Custom update logic for crypto
                clearCacheByKey('crypto_data_daily');
                cryptoIndicators.value = [];
                await fetchCryptoData();
                break;
            case 'calendar':
                await fetchCalendarData();
                break;
        }
    } catch (e) {
        console.error("Error refreshing data:", e);
    } finally {
        loading.value = false;
    }
};

defineExpose({
    refresh: updateData
});


// getIndexChartData moved to IndicesSection

// Bond Chart Options
// Bond logic managed in BondMarketSection

// Energy Chart Options
const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
      legend: {
          position: 'right',
          labels: { 
            color: '#000000',
            generateLabels: function(chart) {
              const data = chart.data;
              if (data.labels.length && data.datasets.length) {
                const dataset = data.datasets[0];
                const total = dataset.data.reduce((a, b) => a + b, 0);
                return data.labels.map((label, i) => {
                  const value = dataset.data[i];
                  const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                  return {
                    text: `${label}: ${percentage}%`,
                    fillStyle: dataset.backgroundColor[i],
                    hidden: false,
                    index: i
                  };
                });
              }
              return [];
            }
          }
      },
      tooltip: {
          callbacks: {
              label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  const total = context.chart._metasets[context.datasetIndex].total;
                  const percentage = Math.round((value / total) * 100) + '%';
                  return `${label}: ${value} (${percentage})`;
              }
          }
      }
  }
};

const energyLineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
      y: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } },
      x: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } }
  },
  plugins: {
      legend: { labels: { color: '#000000' } }
  }
};

const generationData = computed(() => ({
    labels: generation.value.map(i => i.type),
                datasets: [{
        data: generation.value.map(i => i.value),
        backgroundColor: generation.value.map(i => i.color)
    }]
}));

const consumptionData = computed(() => ({
    labels: consumption.value.map(i => i.sector),
    datasets: [{
        data: consumption.value.map(i => i.value),
        backgroundColor: consumption.value.map(i => i.color)
    }]
}));

const demandCurveData = computed(() => {
    if (!gridData.value.hourly_demand) return { labels: [], datasets: [] };
    return {
        labels: gridData.value.hourly_demand.map(i => i.time),
        datasets: [{
            label: 'Demand (MW)',
            data: gridData.value.hourly_demand.map(i => i.demand),
                    borderColor: '#3498db',
            backgroundColor: '#3498db',
            fill: false,
            tension: 0.4
        }]
    };
});





// Economic Chart Options
const economicChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { 
      mode: 'index', 
      intersect: false,
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      titleColor: '#000000',
      bodyColor: '#000000',
      borderColor: '#cccccc',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
      borderWidth: 1,
      padding: 12
    }
  },
  scales: {
    x: { 
      display: true,
      ticks: { 
        color: '#666666', 
        font: { size: 10 },
        maxRotation: 45,
        minRotation: 45
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    },
    y: { 
      display: true,
      ticks: { 
        color: '#666666', 
        font: { size: 10 }
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    }
  },
  elements: {
    point: { 
      radius: 0, 
      hitRadius: 10, 
      hoverRadius: 4
    },
    line: { 
      borderWidth: 2, 
      tension: 0.2 
    }
  }
};

const barChartOptions = {
  ...economicChartOptions,
  elements: {
      ...economicChartOptions.elements,
      bar: {
          borderRadius: 4
      }
  }
};

const getFedChartData = (item) => {
    if (item.chart_type === 'bar') {
    return {
            labels: item.history.map(h => h.date),
        datasets: [{
                label: item.indicator,
                data: item.history.map(h => h.value),
                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                borderColor: '#3498db',
                borderWidth: 1
            }]
        };
    } else {
        return {
            labels: item.history.map(h => h.date),
            datasets: [{
                label: item.indicator,
                data: item.history.map(h => h.value),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                fill: false,
                tension: 0.4
            }]
        };
    }
};

const getEconomicChartData = (item) => {
    if (item.chart_type === 'bar') {
        return {
            labels: item.history.map(h => h.date),
            datasets: [{
                label: item.indicator,
                backgroundColor: '#3498db',
                data: item.history.map(h => h.value)
            }]
        };
    }

    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    return {
        labels: sortedHistory.map(h => h.date),
        datasets: [
            {
                label: item.indicator,
                backgroundColor: '#42b983',
                borderColor: '#42b983',
                data: sortedHistory.map(h => h.value),
                fill: false
            }
        ]
    }
}

// Calculate daily change percentage for crypto
const getCryptoDailyChange = (item) => {
    if (!item.history || item.history.length < 2) {
        return null;
    }
    
    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    const currentPrice = sortedHistory[sortedHistory.length - 1]?.value;
    const previousPrice = sortedHistory[sortedHistory.length - 2]?.value;
    
    if (!currentPrice || !previousPrice || previousPrice === 0) {
        return null;
    }
    
    const change = ((currentPrice - previousPrice) / previousPrice) * 100;
    return change;
}

// Calculate daily change percentage for currency
const getCurrencyDailyChange = (item) => {
    if (!item.history || item.history.length < 2) {
        return null;
    }
    
    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    const currentPrice = sortedHistory[sortedHistory.length - 1]?.value;
    const previousPrice = sortedHistory[sortedHistory.length - 2]?.value;
    
    if (!currentPrice || !previousPrice || previousPrice === 0) {
        return null;
    }
    
    const change = ((currentPrice - previousPrice) / previousPrice) * 100;
    return change;
}

// Calculate daily change percentage for commodity
const getCommodityDailyChange = (item) => {
    if (!item.history || item.history.length < 2) {
        return null;
    }
    
    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    const currentPrice = sortedHistory[sortedHistory.length - 1]?.value;
    const previousPrice = sortedHistory[sortedHistory.length - 2]?.value;
    
    if (!currentPrice || !previousPrice || previousPrice === 0) {
        return null;
    }
    
    const change = ((currentPrice - previousPrice) / previousPrice) * 100;
    return change;
}

// Calculate daily change percentage for bond
// getBondDailyChange removed

// Crypto Chart Data with Volume
const getCryptoChartData = (item) => {
    const sortedHistory = [...(item.history || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Check if volume data exists and has meaningful values (not all zeros)
    const hasVolume = sortedHistory.length > 0 && 
                     sortedHistory[0].volume !== undefined && 
                     sortedHistory.some(h => h.volume && h.volume > 0);
    
    const datasets = [
        {
            label: 'Price',
            data: sortedHistory.map(h => h.value),
            borderColor: '#42b983',
            backgroundColor: 'rgba(66, 185, 131, 0.1)',
            yAxisID: 'y',
            fill: false,
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 2
        }
    ];
    
    // Add volume as a line on secondary axis if available
    if (hasVolume) {
        datasets.push({
            label: 'Volume',
            data: sortedHistory.map(h => h.volume || 0),
            borderColor: 'rgba(52, 152, 219, 0.5)',
            backgroundColor: 'rgba(52, 152, 219, 0.2)',
            yAxisID: 'y1',
            fill: true,
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 1,
            order: 2
        });
    }
    
    return {
        labels: sortedHistory.map(h => h.date),
        datasets: datasets
    }
}

// Crypto Chart Options with dual y-axes
const cryptoChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: { 
      display: true,
      position: 'top',
      labels: {
        color: '#000000',
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: { 
      mode: 'index', 
      intersect: false,
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      titleColor: '#000000',
      bodyColor: '#000000',
      borderColor: '#cccccc',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
      borderWidth: 1,
      padding: 12,
      callbacks: {
        label: function(context) {
          let label = context.dataset.label || '';
          if (label) {
            label += ': ';
          }
          if (context.parsed.y !== null) {
            if (label === 'Volume: ') {
              // Format volume with commas
              label += context.parsed.y.toLocaleString('en-US');
            } else {
              // Format price with 2 decimal places
              label += context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
          }
          return label;
        }
      }
    }
  },
  scales: {
    x: { 
      display: true,
      ticks: { 
        color: '#666666', 
        font: { size: 10 },
        maxRotation: 45,
        minRotation: 45
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    },
    y: { 
      type: 'linear',
      display: true,
      position: 'left',
      ticks: { 
        color: '#42b983',
        font: { size: 10 },
        callback: function(value) {
          return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      },
      title: {
        display: true,
        text: 'Price (USD)',
        color: '#42b983',
        font: { size: 11, weight: 'bold' }
      }
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      ticks: { 
        color: '#3498db',
        font: { size: 10 },
        callback: function(value) {
          // Format large numbers with K, M, B suffixes
          if (value >= 1000000000) {
            return (value / 1000000000).toFixed(1) + 'B';
          } else if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
          } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
          }
          return value.toLocaleString('en-US');
        }
      },
      grid: { 
        drawOnChartArea: false
      },
      title: {
        display: true,
        text: 'Volume',
        color: '#3498db',
        font: { size: 11, weight: 'bold' }
      }
    }
  },
  elements: {
    point: { 
      radius: 0, 
      hitRadius: 10, 
      hoverRadius: 4
    },
    line: { 
      borderWidth: 2, 
      tension: 0.2 
    },
    bar: {
      borderRadius: 2,
      borderSkipped: false
    }
  }
};

const fetchEconomicData = async () => {
  economicLoading.value = true;
  economicError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('macro_data_monthly');
  if (cached) {
    console.log('Using cached macro data');
    economicIndicators.value = cached;
    economicLoading.value = false;
    return;
  }
  
  try {
    // Initial fetch of all data with default 'monthly' (1Y) timeframe
    const response = await fetch(`${API_BASE_URL}/api/market/economic/macro?timeframe=monthly`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();
    
    // Initialize with default timeframe state
    const processedData = data.map(item => ({
        ...item,
        selectedTimeframe: 'monthly',
        loading: false
    }));
    
    economicIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('macro_data_monthly', processedData);
    
  } catch (err) {
    economicError.value = err.message;
  } finally {
    economicLoading.value = false;
  }
};

const updateEconomicData = async () => {
  clearCacheByKey('macro_data_monthly');
  await fetchEconomicData();
};

const fetchFedData = async () => {
  fedLoading.value = true;
  fedError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('fed_data_monthly');
  if (cached) {
    console.log('Using cached Fed data');
    fedIndicators.value = cached;
    fedLoading.value = false;
    return;
  }
  
  try {
    // Fetch macro data and filter for FedWatch Tool
    const response = await fetch(`${API_BASE_URL}/api/internal/macro?timeframe=monthly`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();
    
    // Filter only FedWatch Tool
    const fedData = data.filter(item => item.series_id === 'FEDWATCH');
    
    // Initialize with default timeframe state
    const processedData = fedData.map(item => ({
        ...item,
        selectedTimeframe: 'monthly',
        loading: false
    }));
    
    fedIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('fed_data_monthly', processedData);
    
  } catch (err) {
    fedError.value = err.message;
  } finally {
    fedLoading.value = false;
  }
};

const updateFedData = async () => {
  clearCacheByKey('fed_data_monthly');
  await fetchFedData();
};

// Currency data fetching
const fetchCurrencyData = async () => {
  currencyLoading.value = true;
  currencyError.value = null;
  
  // Check daily cache first
  /*
  const cached = getDailyCache('currency_data_monthly');
  if (cached) {
    console.log('Using cached currency data');
    currencyIndicators.value = cached;
    currencyLoading.value = false;
    return;
  }
  */
  
  try {
    // Fetch all currency data from the new endpoint
    const response = await fetch(`${API_BASE_URL}/api/market/currency/`);
    if (!response.ok) throw new Error('Failed to fetch currency data');
    const data = await response.json();
    
    console.log('[CURRENCY] Received data:', data);
    console.log('[CURRENCY] Data length:', data.length);
    
    // Data is already in the correct format from the backend
    const processedData = data.map(item => {
      console.log('[CURRENCY] Processing item:', item.name, 'symbol:', item.symbol);
      return {
        ...item,
        selectedTimeframe: 'monthly',
        loading: false
      };
    });
    
    console.log('[CURRENCY] Processed data:', processedData);
    
    currencyIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('currency_data_monthly', processedData);
    
  } catch (err) {
    currencyError.value = err.message;
  } finally {
    currencyLoading.value = false;
  }
};

const updateCurrencyIndicatorTimeframe = async (item, timeframe) => {
  if (item.selectedTimeframe === timeframe) return;
  
  // Safety check for symbol
  if (!item.symbol) {
    console.error('[CURRENCY] Missing symbol for item:', item);
    return;
  }
  
  item.selectedTimeframe = timeframe;
  item.loading = true;
  
  // Check cache
  const cached = getEconomicCachedData(item.symbol, timeframe);
  if (cached) {
    Object.assign(item, cached);
    item.selectedTimeframe = timeframe;
    item.loading = false;
    return;
  }
  
  try {
    console.log('[CURRENCY] Fetching timeframe data for:', item.symbol, 'timeframe:', timeframe);
    // Use the new currency endpoint
    const response = await fetch(`${API_BASE_URL}/api/market/currency/${item.symbol}?timeframe=${timeframe}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();
    
    item.history = data.history || [];
    item.value = data.value;
    item.date = data.date;
    item.selectedTimeframe = timeframe;
    
    // Cache the data
    setEconomicCachedData(item.series_id, timeframe, {
      history: item.history,
      value: item.value,
      date: item.date,
      selectedTimeframe: timeframe
    });
  } catch (err) {
    console.error(`Error fetching ${item.indicator}:`, err);
  } finally {
    item.loading = false;
  }
};

// Commodity data fetching
const fetchCommodityData = async () => {
  commodityLoading.value = true;
  commodityError.value = null;
  
  // Check daily cache first
  // Cache disabled for debugging
  /*
  const cached = getDailyCache('commodity_data_monthly');
  if (cached && typeof cached === 'object' && Object.keys(cached).length > 0) {
    console.log('Using cached commodity data');
    commodityIndicators.value = cached;
    commodityLoading.value = false;
    return;
  } else if (cached) {
    console.warn('[COMMODITY] Cached data is invalid/empty, refetching...');
    localStorage.removeItem('commodity_data_monthly');
  }
  */
  
  try {
    console.log('[COMMODITY] Fetching from:', `${API_BASE_URL}/api/market/commodity/`);
    
    // Fetch all commodity data from the new endpoint
    const response = await fetch(`${API_BASE_URL}/api/market/commodity/`);
    if (!response.ok) {
      console.error('[COMMODITY] HTTP Error:', response.status, response.statusText);
      throw new Error(`Failed to fetch commodity data: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('[COMMODITY] Received data:', data);
    console.log('[COMMODITY] Data keys:', Object.keys(data));
    
    // Transform the data to match our frontend structure
    // Backend returns: { "Financials": [...], "Metals": [...], etc }
    // Frontend expects: { financials: [...], metals: [...], etc }
    const processedData = {};
    
    // Map backend category names to frontend keys
    const categoryMap = {
      'Financials': 'financials',
      'Metals': 'metals',
      'Energy': 'energy',
      'Agriculture': 'agricultural',
      'Softs & Livestock': 'softs',
    };
    
    for (const [backendKey, frontendKey] of Object.entries(categoryMap)) {
      const items = data[backendKey] || [];
      console.log(`[COMMODITY] Processing ${backendKey}:`, items.length, 'items');
      
      processedData[frontendKey] = items.map(item => ({
        indicator: item.name,
        value: item.price,
        date: item.history && item.history.length > 0 ? item.history[item.history.length - 1].date : new Date().toISOString().split('T')[0],
        description: `${item.name} (${item.type})`,
        series_id: item.symbol,
        history: item.history || [],
        selectedTimeframe: 'monthly',
        loading: false
      }));
    }
    
    console.log('[COMMODITY] Processed data:', processedData);
    console.log('[COMMODITY] Financials count:', processedData.financials?.length || 0);
    
    commodityIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('commodity_data_monthly', processedData);
    
  } catch (err) {
    console.error('[COMMODITY] Error:', err);
    commodityError.value = err.message;
  } finally {
    commodityLoading.value = false;
  }
};

const updateCommodityIndicatorTimeframe = async (item, timeframe) => {
  if (item.selectedTimeframe === timeframe) return;
  
  item.selectedTimeframe = timeframe;
  item.loading = true;
  
  // Check cache
  const cached = getEconomicCachedData(item.series_id, timeframe);
  if (cached) {
    Object.assign(item, cached);
    item.selectedTimeframe = timeframe;
    item.loading = false;
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();
    
    item.history = data.history || [];
    item.value = data.value;
    item.date = data.date;
    item.selectedTimeframe = timeframe;
    
    // Cache the data
    setEconomicCachedData(item.series_id, timeframe, {
      history: item.history,
      value: item.value,
      date: item.date,
      selectedTimeframe: timeframe
    });
  } catch (err) {
    console.error(`Error fetching ${item.indicator}:`, err);
  } finally {
    item.loading = false;
  }
};

// Crypto data fetching
const fetchCryptoData = async () => {
  cryptoLoading.value = true;
  cryptoError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('crypto_data_daily');
  if (cached) {
    console.log('Using cached crypto data');
    // Ensure history is preserved from cache (like Bond/Economic tabs)
    const processedCached = cached.map(item => ({
      ...item,
      history: item.history || [], // Ensure history is always an array
      selectedTimeframe: item.selectedTimeframe || 'daily',
      loading: false
    }));
    
    cryptoIndicators.value = processedCached;
    cryptoLoading.value = false;
    return;
  }
  
  try {
    // Fetch data WITH history (like Bond/Economic tabs) - default timeframe is 'daily'
    const response = await fetch(`${API_BASE_URL}/api/market/crypto/all?timeframe=daily`);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[ERROR] Backend returned error:', response.status, errorText);
      throw new Error(`Failed to fetch crypto data: ${response.status} ${errorText}`);
    }
    const cryptoData = await response.json();
    
    // Validate that cryptoData is an array
    if (!Array.isArray(cryptoData)) {
      console.error('[ERROR] Backend did not return an array. Received:', typeof cryptoData, cryptoData);
      
      // If it's an object with a detail/error message, extract it
      if (cryptoData && typeof cryptoData === 'object') {
        const errorMsg = cryptoData.detail || cryptoData.error || cryptoData.message || JSON.stringify(cryptoData);
        throw new Error(`Invalid response format: ${errorMsg}`);
      }
      
      throw new Error(`Invalid response format: expected array, got ${typeof cryptoData}`);
    }
    
    console.log('[DEBUG] Received crypto data from backend:', cryptoData.length, 'items');
    
    // Process data - history is already included in the response (like Bond/Economic)
    const processedData = cryptoData.map(item => ({
      ...item,
      history: item.history || [], // History is already included from backend
      selectedTimeframe: item.selectedTimeframe || 'daily', // Default timeframe
      loading: false
    }));
    
    cryptoIndicators.value = processedData;
    
    // Cache data with history (like Bond/Economic tabs)
    setDailyCache('crypto_data_daily', processedData);
    
  } catch (err) {
    console.error('[ERROR] Failed to fetch crypto data:', err);
    cryptoError.value = err.message;
  } finally {
    cryptoLoading.value = false;
  }
};

const updateCryptoIndicatorTimeframe = async (item, timeframe) => {
  if (item.selectedTimeframe === timeframe && item.history && item.history.length > 0) return;
  
  item.selectedTimeframe = timeframe;
  item.loading = true;
  
  // Check cache
  const cached = getEconomicCachedData(item.series_id, timeframe);
  if (cached && cached.history && cached.history.length > 0) {
    item.history = cached.history;
    item.value = cached.value || item.value;
    item.volume = cached.volume || item.volume;
    item.date = cached.date || item.date;
    item.selectedTimeframe = timeframe;
    item.loading = false;
    return;
  }
  
  try {
    // Fetch history data from crypto endpoint (like Bond/Economic tabs)
    const historyResponse = await fetch(`${API_BASE_URL}/api/market/crypto/${item.series_id}/history?period=${timeframe}`);
    if (!historyResponse.ok) throw new Error('Failed to fetch crypto history');
    
    const historyData = await historyResponse.json();
    
    item.history = historyData.history || [];
    item.value = historyData.value || item.value; // Update price if available, otherwise keep current
    item.volume = historyData.volume || item.volume;
    item.date = historyData.date || item.date;
    item.selectedTimeframe = timeframe;
    
    // Cache the data (including volume)
    setEconomicCachedData(item.series_id, timeframe, {
      history: item.history,
      value: item.value,
      volume: item.volume,
      date: item.date,
      selectedTimeframe: timeframe
    });
  } catch (err) {
    console.error(`Error fetching ${item.indicator} history:`, err);
    item.history = []; // Clear history on error
  } finally {
    item.loading = false;
  }
};

const updateFedIndicatorTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getEconomicCachedData(item.series_id, timeframe);
    if (cached) {
        Object.assign(item, cached);
        item.selectedTimeframe = timeframe;
        item.loading = false;
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch data');
        const data = await response.json();
        
        item.history = data.history || [];
        item.value = data.value;
        item.date = data.date;
        item.selectedTimeframe = timeframe;
        
        // Cache the data
        setEconomicCachedData(item.series_id, timeframe, {
            history: item.history,
            value: item.value,
            date: item.date,
            selectedTimeframe: timeframe
        });
    } catch (err) {
        console.error(`Error fetching ${item.indicator}:`, err);
    } finally {
        item.loading = false;
    }
};

const updateIndicatorTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getEconomicCachedData(item.series_id, timeframe);
    if (cached) {
        Object.assign(item, cached);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        item.loading = false;
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch series');
        const data = await response.json();
        
        // Update item properties with new data
        Object.assign(item, data);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        
        setEconomicCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.indicator}:`, err);
    } finally {
        item.loading = false;
    }
};

// Watch for tab changes to fetch short interest data
// Calendar data fetching
const calendarLoading = ref(false);
const calendarError = ref(null);
const calendarData = ref([]);

const fetchCalendarData = async () => {
    calendarLoading.value = true;
    calendarError.value = null;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/framework/economic-calendar`);
        if (!response.ok) throw new Error('Failed to fetch calendar data');
        const data = await response.json();
        calendarData.value = data;
    } catch (err) {
        console.error('Error fetching calendar data:', err);
        calendarError.value = err.message;
    } finally {
        calendarLoading.value = false;
    }
}

// Calendar Filtering
const calendarImpacts = ['Low', 'Medium', 'High', 'None'];
const selectedImpacts = ref(['High']);
const calendarCountries = computed(() => {
    if (!calendarData.value) return ['US', 'JP'];
    const countries = new Set(calendarData.value.map(item => item.country).filter(c => c));
    return Array.from(countries).sort();
});
const selectedCountries = ref(['US', 'JP']);
const showImpactDropdown = ref(false);
const showCountryDropdown = ref(false);

const filteredCalendarData = computed(() => {
    if (!calendarData.value) return [];
    return calendarData.value.filter(item => {
        const impactMatch = selectedImpacts.value.length === 0 || selectedImpacts.value.includes(item.impact);
        const countryMatch = selectedCountries.value.length === 0 || selectedCountries.value.includes(item.country);
        return impactMatch && countryMatch;
    });
});

const toggleImpact = (impact) => {
    if (selectedImpacts.value.includes(impact)) {
        selectedImpacts.value = selectedImpacts.value.filter(i => i !== impact);
    } else {
        selectedImpacts.value.push(impact);
    }
}

const toggleCountry = (country) => {
    if (selectedCountries.value.includes(country)) {
        selectedCountries.value = selectedCountries.value.filter(c => c !== country);
    } else {
        selectedCountries.value.push(country);
    }
}

// Economic expandable list functions
const toggleEconomicItem = (index) => {
    const newSet = new Set(expandedEconomicItems.value);
    if (newSet.has(index)) {
        newSet.delete(index);
    } else {
        newSet.add(index);
    }
    expandedEconomicItems.value = newSet;
};

const formatEconomicValue = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
        return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return value;
};

const getRecentHistory = (history) => {
    if (!history || history.length === 0) return [];
    // Return last 10 items, sorted by date descending
    return [...history]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10);
};

const getEconomicFrequency = (seriesId) => {
    const frequencies = {
        'GDP': 'Quarterly',
        'realGDP': 'Quarterly',
        'nominalPotentialGDP': 'Quarterly',
        'realGDPPerCapita': 'Quarterly',
        'federalFunds': 'Monthly',
        'CPI': 'Monthly',
        'inflationRate': 'Monthly',
        'inflation': 'Monthly',
        'retailSales': 'Monthly',
        'consumerSentiment': 'Monthly',
        'durableGoods': 'Monthly',
        'unemploymentRate': 'Monthly',
        'totalNonfarmPayroll': 'Monthly',
        'initialClaims': 'Weekly',
        'industrialProductionTotalIndex': 'Monthly',
        'newPrivatelyOwnedHousingUnitsStartedTotalUnits': 'Monthly',
        'totalVehicleSales': 'Monthly',
        'retailMoneyFunds': 'Weekly',
        'smoothedUSRecessionProbabilities': 'Monthly',
        '3MonthOr90DayRatesAndYieldsCertificatesOfDeposit': 'Daily',
        'commercialBankInterestRateOnCreditCardPlansAllAccounts': 'Quarterly',
        '30YearFixedRateMortgageAverage': 'Weekly',
        '15YearFixedRateMortgageAverage': 'Weekly',
        'tradeBalanceGoodsAndServices': 'Monthly'
    };
    return frequencies[seriesId] || 'Monthly';
};

const getNextReleaseDate = (seriesId, lastDate) => {
    if (!lastDate) return 'TBD';
    
    const frequency = getEconomicFrequency(seriesId);
    const last = new Date(lastDate);
    let next = new Date(last);
    
    switch (frequency) {
        case 'Weekly':
            next.setDate(next.getDate() + 7);
            break;
        case 'Monthly':
            next.setMonth(next.getMonth() + 1);
            break;
        case 'Quarterly':
            next.setMonth(next.getMonth() + 3);
            break;
        case 'Daily':
            next.setDate(next.getDate() + 1);
            break;
        default:
            return 'TBD';
    }
    
    return next.toISOString().split('T')[0];
};

const getEconomicSource = (seriesId) => {
    const sources = {
        'GDP': 'Bureau of Economic Analysis (BEA)',
        'realGDP': 'Bureau of Economic Analysis (BEA)',
        'nominalPotentialGDP': 'Congressional Budget Office (CBO)',
        'realGDPPerCapita': 'Bureau of Economic Analysis (BEA)',
        'federalFunds': 'Federal Reserve',
        'CPI': 'Bureau of Labor Statistics (BLS)',
        'inflationRate': 'Bureau of Labor Statistics (BLS)',
        'inflation': 'Bureau of Labor Statistics (BLS)',
        'retailSales': 'U.S. Census Bureau',
        'consumerSentiment': 'University of Michigan',
        'durableGoods': 'U.S. Census Bureau',
        'unemploymentRate': 'Bureau of Labor Statistics (BLS)',
        'totalNonfarmPayroll': 'Bureau of Labor Statistics (BLS)',
        'initialClaims': 'Department of Labor',
        'industrialProductionTotalIndex': 'Federal Reserve',
        'newPrivatelyOwnedHousingUnitsStartedTotalUnits': 'U.S. Census Bureau',
        'totalVehicleSales': 'Bureau of Economic Analysis (BEA)',
        'retailMoneyFunds': 'Federal Reserve',
        'smoothedUSRecessionProbabilities': 'Federal Reserve Bank',
        '3MonthOr90DayRatesAndYieldsCertificatesOfDeposit': 'Federal Reserve',
        'commercialBankInterestRateOnCreditCardPlansAllAccounts': 'Federal Reserve',
        '30YearFixedRateMortgageAverage': 'Freddie Mac',
        '15YearFixedRateMortgageAverage': 'Freddie Mac',
        'tradeBalanceGoodsAndServices': 'U.S. Census Bureau'
    };
    return sources[seriesId] || 'Financial Modeling Prep';
};

const eventSource = ref(null);

const setupStream = () => {
    if (eventSource.value) return;
    
    // Connect to SSE endpoint
    const url = `${API_BASE_URL}/api/stream/market`;
    console.log('Connecting to SSE:', url);
    eventSource.value = new EventSource(url);
    
    eventSource.value.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            handleStreamUpdate(payload);
        } catch (e) {
            console.error('SSE Parse Error:', e);
        }
    };
    
    eventSource.value.onerror = (e) => {
        console.warn('SSE Connection lost, retrying in 5s...');
        if (eventSource.value) {
            eventSource.value.close();
            eventSource.value = null;
        }
        setTimeout(setupStream, 5000);
    };
};

const handleStreamUpdate = (payload) => {
    if (!payload || !payload.type) return;
    
    switch (payload.type) {
        case 'indices_regional':
            if (indicesRef.value && indicesRef.value.updateData) {
                console.log('Received regional indices update');
                indicesRef.value.updateData(payload.data);
            }
            break;
        case 'indices_major':
            // Logic for major indices if displayed
            break;
    }
};

// Watch for tab changes logic
watch(activeTab, (newTab) => {
    loadTabContent(newTab);
    // startAutoRefresh(); // Replaced by SSE
});

import { onUnmounted } from 'vue';

onMounted(() => {
    loadTabContent(activeTab.value);
    setupStream();
});

onUnmounted(() => {
    if (eventSource.value) {
        eventSource.value.close();
    }
});
</script>

<style scoped>
.dashboard {
  padding: 20px 20px 20px 0;
  max-width: 1800px;
  margin: 0 auto;
  background: #ffffff;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.update-btn {
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

.update-btn:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-1px);
}

.update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}


.indices-section {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 30px;
}

@media (max-width: 1200px) {
    .indices-section {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .indices-section {
        grid-template-columns: 1fr;
    }
}

.index-card {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    color: #000000;
    text-align: center;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.index-card h3 {
    margin: 0 0 10px 0;
    font-size: 1em;
    color: #000000;
    font-weight: 600;
}

.index-value {
    font-size: 1.8em;
    font-weight: bold;
    margin: 8px 0;
}

.index-change {
    font-size: 1.1em;
    font-weight: 600;
    margin: 5px 0 15px 0;
}

.mini-chart {
    height: 120px;
    margin-top: 10px;
}

.market-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}

@media (max-width: 1400px) {
    .market-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .market-grid {
        grid-template-columns: 1fr;
    }
}
.market-section {
    background: #ffffff;
    padding: 15px;
    border-radius: 8px;
    color: #000000;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.market-section h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.market-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.market-table th {
    text-align: left;
    color: #666666;
    font-size: 0.9em;
    padding-bottom: 5px;
    border-bottom: 1px solid #cccccc;
    font-weight: 600;
}

.market-table td {
    padding: 8px 0;
    font-size: 0.95em;
    color: #000000;
}

.ticker-cell {
    font-weight: bold;
    color: #3498db;
    cursor: pointer;
    text-decoration: underline;
}

.ticker-cell:hover {
    color: #2980b9;
}
.positive { color: #42b983; }
.negative { color: #e74c3c; }

.hover-chart-tooltip {
    position: fixed;
    background: #ffffff;
    border: 1px solid #cccccc;
    padding: 10px;
    border-radius: 8px;
    z-index: 9999;
    width: 250px;
    height: 150px;
    pointer-events: none; /* Let mouse events pass through so we don't trigger leave */
    box-shadow: 0 4px 6px rgba(0,0,0,0.15);
}

.hover-chart-tooltip h4 {
    margin: 0 0 5px 0;
    font-size: 0.9em;
    color: #000000;
    text-align: center;
    font-weight: 600;
}
.chart-wrapper {
    height: 100px;
    width: 100%;
}

/* Key Logs Section Styles */
.key-logs-section {
    background: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.key-logs-header {
    margin-bottom: 20px;
}

.key-logs-header h2 {
    margin: 0;
    color: #000000;
    font-weight: 600;
    font-size: 1.5em;
}

.tab-selector {
    display: flex;
    gap: 0;
    border-bottom: 2px solid #cccccc;
    margin-bottom: 20px;
}

.tab-btn {
    padding: 12px 24px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: #666666;
    font-size: 1em;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
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
    padding: 0;
}

.tab-placeholder {
    padding: 40px;
    text-align: center;
    color: #666666;
}

.tab-placeholder h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.tab-placeholder p {
    margin: 10px 0;
    line-height: 1.6;
}

.placeholder-note {
    font-style: italic;
    color: #999999;
    font-size: 0.9em;
}

/* Bond Tab Styles */
.bond-tab-content {
    padding: 0;
}


.category-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 30px;
    justify-content: center;
    flex-wrap: nowrap;
    border-bottom: 2px solid #cccccc;
    padding-bottom: 12px;
    overflow-x: auto;
}

.category-tabs button {
    background: transparent;
    border: none;
    color: #666666;
    padding: 12px 20px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 0.95em;
    font-weight: 500;
    transition: all 0.2s;
    border-bottom: 3px solid transparent;
}

.category-tabs button.active {
    color: #000000;
    border-bottom-color: #3498db;
    background: rgba(52, 152, 219, 0.1);
    font-weight: 600;
}

.category-tabs button:hover {
    color: #000000;
    background: rgba(0, 0, 0, 0.05);
}

.category-section {
    margin-top: 20px;
}

.category-title {
    font-size: 1.5em;
    color: #000000;
    margin-bottom: 24px;
    text-align: center;
    font-weight: 600;
}

.indicators-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
}

@media (max-width: 1200px) {
    .indicators-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .indicators-grid {
        grid-template-columns: 1fr;
    }
}

.bond-card {
    border: 1px solid #cccccc;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    background: #ffffff;
    color: #000000;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
}

.bond-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.bond-card h4 {
    margin: 0 0 12px 0;
    font-size: 1.1em;
    font-weight: 600;
    color: #000000;
}

.card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.value {
    font-size: 2em;
    font-weight: bold;
    color: #42b983;
    margin: 8px 0;
}

.date {
    font-size: 0.85em;
    color: #666666;
    margin: 4px 0;
}

.desc {
    font-size: 0.9em;
    font-style: italic;
    margin: 8px 0 16px 0;
    color: #666666;
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.daily-change {
    font-size: 0.95em;
    font-weight: 600;
    font-style: normal;
    margin-left: 8px;
}

.card-timeframe-selector {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 16px;
}

.card-timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75em;
    transition: all 0.2s;
}

.card-timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.card-timeframe-selector button:hover:not(.active) {
    background: #e9ecef;
}

.chart-container {
    height: 250px;
    width: 100%;
    margin-top: auto;
    padding-top: 16px;
    position: relative;
}

.chart-container.large-chart {
    height: 350px;
}

.chart-loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
}

.spinner-small {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(0, 0, 0, 0.1);
    border-top-color: #42b983;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: #000000;
}

.loading-state p {
    color: #666666;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #cccccc;
    border-top-color: #42b983;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.error-state {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
}

.error-message {
    color: #e74c3c;
    font-size: 1.1em;
    background: rgba(231, 76, 60, 0.1);
    padding: 16px 24px;
    border-radius: 8px;
    border: 1px solid #e74c3c;
}

.no-data {
    height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666666;
    font-style: italic;
}

/* Economic Tab Styles */
.economic-tab-content {
    padding: 0;
}


.indicators {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    max-width: 1600px;
    margin: 0 auto;
}

@media (max-width: 1200px) {
    .indicators {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .indicators {
        grid-template-columns: 1fr;
    }
}

.indicator-card {
    border: 1px solid #cccccc;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    background: #ffffff;
    color: #000000;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
}

.indicator-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.indicator-card h3 {
    margin: 0 0 12px 0;
    font-size: 1.1em;
    font-weight: 600;
    color: #000000;
}

/* Fed Tab Styles */
.liquidity-subsection {
    margin-bottom: 40px;
}

.subsection-title {
    font-size: 1.3em;
    font-weight: 600;
    color: #000000;
    margin-bottom: 16px;
    margin-top: 0;
}

.liquidity-table {
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
}

.liquidity-table thead {
    background-color: #f5f5f5;
}

.liquidity-table th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    color: #000000;
    border-bottom: 2px solid #cccccc;
    font-size: 0.95em;
}

.liquidity-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #e0e0e0;
    color: #000000;
    font-size: 0.9em;
}

.liquidity-table tbody tr:last-child td {
    border-bottom: none;
}

.liquidity-table tbody tr:hover {
    background-color: #f9f9f9;
}

.liquidity-table a {
    color: #3498db;
    text-decoration: none;
    word-break: break-all;
}

.liquidity-table a:hover {
    text-decoration: underline;
    color: #2980b9;
}

/* Policy Tab Styles */
.policy-tab-content {
    padding: 20px;
}

.policy-section {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
}

.section-title {
    font-size: 1.5em;
    font-weight: 600;
    color: #000000;
    margin-bottom: 20px;
}

.placeholder-message {
    color: #666666;
    font-size: 1em;
    text-align: center;
    padding: 40px 20px;
}

/* Energy Tab Styles */
.energy-tab-content {
    padding: 0;
}


.energy-layout {
    display: flex;
    gap: 15px;
    width: 100%;
    box-sizing: border-box;
}

.energy-layout .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
    min-width: 0;
}

.energy-layout .sidebar {
    flex: 0 0 25%;
    display: flex;
    flex-direction: column;
    gap: 15px;
    min-width: 300px;
}

@media (max-width: 1200px) {
    .energy-layout {
        flex-direction: column;
    }
    
    .energy-layout .sidebar {
        width: 100%;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .energy-layout .sidebar {
        grid-template-columns: 1fr;
    }
}

.energy-layout .card {
    background: #ffffff;
    color: #000000;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.energy-layout .card h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.energy-layout .full-width {
    width: 100%;
}

.energy-layout .chart-container {
    height: 300px;
    position: relative;
}

.energy-layout .sidebar .chart-container {
    height: 250px;
}

.energy-layout .chart-container-small {
    height: 200px;
    margin-top: 20px;
}

.energy-layout .metrics p {
    margin: 5px 0;
    color: #000000;
}

.energy-layout .metrics strong {
    color: #000000;
}

.energy-layout .timeframe-selector {
    display: flex;
    gap: 10px;
    margin: 15px 0;
    justify-content: center;
}

.energy-layout .timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    transition: all 0.2s;
}

.energy-layout .timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.energy-layout .timeframe-selector button:hover {
    background: #e9ecef;
}

/* Currency Tab Styles */
.currency-tab-content {
    padding: 0;
}

.currency-data {
    margin-top: 20px;
}

.currency-timeframe-selector {
    display: flex;
    gap: 10px;
    margin-bottom: 30px;
    justify-content: center;
    padding: 10px 0;
}

.currency-timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    font-weight: 500;
    transition: all 0.2s;
}

.currency-timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.currency-timeframe-selector button:hover:not(.active) {
    background: #e9ecef;
}

.currency-value-display {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin-top: 15px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #cccccc;
}

.currency-label {
    font-size: 0.95em;
    color: #666666;
    font-weight: 500;
}

.currency-value {
    font-size: 1.3em;
    color: #000000;
    font-weight: 600;
}

/* Commodity Tab Styles */
.commodity-tab-content {
    padding: 0;
}

.commodity-data {
    margin-top: 20px;
}

.commodity-timeframe-selector {
    display: flex;
    gap: 10px;
    margin-bottom: 30px;
    justify-content: center;
    padding: 10px 0;
}

.commodity-timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9em;
    font-weight: 500;
    transition: all 0.2s;
}

.commodity-timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.commodity-timeframe-selector button:hover:not(.active) {
    background: #e9ecef;
}

/* Crypto Tab Styles */
.crypto-tab-content {
    padding: 0;
}

.crypto-data {
    margin-top: 20px;
}

/* Short Interest Tab Styles */

</style>

<style scoped>
.calendar-filters {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e5e5e5;
}

.filter-group {
    display: flex;
    align-items: center;
    gap: 10px;
}

.filter-label {
    font-weight: 600;
    color: #4b5563;
    font-size: 0.9rem;
}

.filter-options {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.filter-btn {
    padding: 6px 14px;
    border: 1px solid #d1d5db;
    background: #ffffff;
    border-radius: 16px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    color: #4b5563;
}

.filter-btn.active {
    background: #111827; /* Dark black/grey like title */
    color: white;
    border-color: #111827;
}

.filter-btn:hover:not(.active) {
    background: #f3f4f6;
    border-color: #9ca3af;
}

/* Dropdown Styles */
.custom-dropdown {
    position: relative;
    display: inline-block;
    min-width: 150px;
}

.dropdown-toggle {
    width: 100%;
    padding: 8px 12px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    font-size: 0.9em;
    color: #374151;
}

.dropdown-toggle:hover {
    background: #f9fafb;
}

.dropdown-menu {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 1000;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    margin-top: 4px;
    max-height: 300px;
    overflow-y: auto;
    width: max-content;
    min-width: 100%;
}

.dropdown-item {
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9em;
    color: #374151;
}

.dropdown-item:hover {
    background: #f3f4f6;
}

.dropdown-item.selected {
    background: #eff6ff;
    color: #2563eb;
    font-weight: 500;
}

.check-box {
    width: 16px;
    display: inline-block;
}

.chevron {
    font-size: 0.8em;
    margin-left: 8px;
    color: #6b7280;
}

/* Economic List Styles */
.economic-list-container {
    max-width: 100%;
    padding: 20px;
}

.economic-item {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.economic-item:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.economic-item.expanded {
    border-color: #3b82f6;
}

.economic-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    cursor: pointer;
    user-select: none;
    transition: background-color 0.2s ease;
}

.economic-header:hover {
    background-color: #f9fafb;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
}

.expand-icon {
    color: #6b7280;
    font-size: 12px;
    width: 16px;
    display: inline-block;
    transition: transform 0.3s ease;
}

.indicator-name {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #111827;
}

.category-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    text-transform: capitalize;
}

.category-macro {
    background-color: #dbeafe;
    color: #1e40af;
}

.category-labor {
    background-color: #fef3c7;
    color: #92400e;
}

.category-business {
    background-color: #d1fae5;
    color: #065f46;
}

.category-housing {
    background-color: #fce7f3;
    color: #9f1239;
}

.category-financial {
    background-color: #e0e7ff;
    color: #3730a3;
}

.category-monetary {
    background-color: #fef2f2;
    color: #991b1b;
}

.category-rates {
    background-color: #f3e8ff;
    color: #6b21a8;
}

.category-credit {
    background-color: #ffedd5;
    color: #9a3412;
}

.header-right {
    display: flex;
    align-items: center;
}

.current-value {
    font-size: 18px;
    font-weight: 700;
    color: #059669;
}

.economic-details {
    padding: 0 20px 20px 20px;
    background-color: #f9fafb;
    border-top: 1px solid #e5e7eb;
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        max-height: 0;
    }
    to {
        opacity: 1;
        max-height: 1000px;
    }
}

.details-table {
    width: 100%;
    margin-top: 16px;
    border-collapse: collapse;
    background: white;
    border-radius: 6px;
    overflow: hidden;
}

.details-table tr {
    border-bottom: 1px solid #e5e7eb;
}

.details-table tr:last-child {
    border-bottom: none;
}

.label-cell {
    padding: 12px 16px;
    font-weight: 600;
    color: #6b7280;
    width: 200px;
    background-color: #f9fafb;
}

.value-cell {
    padding: 12px 16px;
    color: #111827;
}

.history-section {
    margin-top: 20px;
}

.history-section h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #374151;
}

.history-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 6px;
    overflow: hidden;
}

.history-table thead {
    background-color: #f3f4f6;
}

.history-table th {
    padding: 10px 16px;
    text-align: left;
    font-weight: 600;
    color: #374151;
    font-size: 13px;
}

.history-table td {
    padding: 10px 16px;
    border-top: 1px solid #e5e7eb;
    color: #111827;
    font-size: 13px;
}

.history-table tbody tr:hover {
    background-color: #f9fafb;
}

</style>
