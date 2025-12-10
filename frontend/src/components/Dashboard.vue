<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Market Dashboard</h1>
      <button @click="updateData" :disabled="loading" class="update-btn">
        {{ loading ? 'Refreshing...' : 'Refresh Data' }}
      </button>
    </div>
    
    <div v-if="loading" class="loading">Loading Market Data...</div>
    <div v-else>
        <!-- Key Logs Section -->
        <div class="key-logs-section">
            <div class="key-logs-header">
                <h2>Key Logs</h2>
            </div>

            <!-- Tab Selector -->
            <div class="tab-selector">
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'equity' }"
                    @click="activeTab = 'equity'"
                >
                    Equity
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'bond' }"
                    @click="activeTab = 'bond'"
                >
                    Bond
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'economic' }"
                    @click="activeTab = 'economic'"
                >
                    Economic
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'fed' }"
                    @click="activeTab = 'fed'"
                >
                    Fed
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'currency' }"
                    @click="activeTab = 'currency'"
                >
                    Currency
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'commodity' }"
                    @click="activeTab = 'commodity'"
                >
                    Commodity
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'crypto' }"
                    @click="activeTab = 'crypto'"
                >
                    Crypto
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'energy' }"
                    @click="activeTab = 'energy'"
                >
                    Energy
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'policy' }"
                    @click="activeTab = 'policy'"
                >
                    Policy
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'short-interest' }"
                    @click="activeTab = 'short-interest'"
                >
                    Short Interest
                </button>
            </div>

            <!-- Equity Tab Content -->
            <div v-if="activeTab === 'equity'" class="tab-content">
        <!-- Index Charts Section -->
        <div class="indices-section">
            <div class="index-card" v-for="index in indices" :key="index.name">
                <h3>{{ index.name }}</h3>
                <div class="index-value" :class="index.change >= 0 ? 'positive' : 'negative'">
                    {{ index.value.toLocaleString() }}
                </div>
                <div class="index-change" :class="index.change >= 0 ? 'positive' : 'negative'">
                    {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }}%
                </div>
                <div class="mini-chart">
                    <Line :data="getIndexChartData(index)" :options="miniChartOptions" />
                </div>
            </div>
        </div>

            </div>

            <!-- Bond Tab Content -->
            <div v-if="activeTab === 'bond'" class="tab-content bond-tab-content">
                <div class="category-tabs">
                    <button 
                        v-for="category in bondCategories" 
                        :key="category.value" 
                        :class="{ active: activeBondCategory === category.value }"
                        @click="activeBondCategory = category.value"
                    >
                        {{ category.label }}
                    </button>
                </div>

                <div v-if="bondLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Bond Market Data...</p>
                </div>
                <div v-else-if="bondError" class="error-state">
                    <p class="error-message">{{ bondError }}</p>
                </div>
                <div v-else class="bond-data">
                    <!-- Treasury Yields -->
                    <div v-if="activeBondCategory === 'treasury_yields'" class="category-section">
                        <h3 class="category-title">Government Bond Market Data - Treasury Yields</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.treasury_yields" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Yield Curve Spreads -->
                    <div v-if="activeBondCategory === 'yield_curve'" class="category-section">
                        <h3 class="category-title">Yield Curve Spreads</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.yield_curve" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }} bps</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- TIPS & Breakeven -->
                    <div v-if="activeBondCategory === 'tips_breakeven'" class="category-section">
                        <h3 class="category-title">Inflation-Linked Bonds (TIPS) & Breakeven Rates</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.tips_breakeven" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Central Bank Rates -->
                    <div v-if="activeBondCategory === 'central_bank_rates'" class="category-section">
                        <h3 class="category-title">Central Bank & Money Market Rates</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.central_bank_rates" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Credit Spreads -->
                    <div v-if="activeBondCategory === 'credit_spreads'" class="category-section">
                        <h3 class="category-title">Credit Market Data - Corporate Bond Spreads</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.credit_spreads" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(2) }} bps</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container large-chart" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Funding Stress -->
                    <div v-if="activeBondCategory === 'funding_stress'" class="category-section">
                        <h3 class="category-title">Funding Stress Metrics</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.funding_stress" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
                                            :key="tf.value" 
                                            :class="{ active: item.selectedTimeframe === tf.value }"
                                            @click="updateBondItemTimeframe(item, tf.value)"
                                            :disabled="item.loading"
                                        >
                                            {{ tf.label }}
                                        </button>
                                    </div>
                                </div>
                                <div class="chart-container" v-if="item.history && item.history.length > 0">
                                    <div v-if="item.loading" class="chart-loading-overlay">
                                        <div class="spinner-small"></div>
                                    </div>
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Economic Tab Content -->
            <div v-if="activeTab === 'economic'" class="tab-content economic-tab-content">
                <div v-if="economicLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Macro Economic Data...</p>
                </div>
                <div v-else-if="economicError" class="error-state">
                    <p class="error-message">{{ economicError }}</p>
                </div>
                <div v-else class="indicators">
                    <div v-for="item in economicIndicators.filter(item => item.series_id !== 'FEDWATCH')" :key="item.indicator" class="indicator-card">
                        <div class="card-content">
                            <h3>{{ item.indicator }}</h3>
                            <p class="value">{{ item.value }}</p>
                            <p class="date">{{ item.date }}</p>
                            <p class="desc">{{ item.description || '&nbsp;' }}</p>
                            
                            <!-- Per-graph Timeframe Selector -->
                            <div class="card-timeframe-selector">
                                <button 
                                    v-for="tf in economicTimeframes" 
                                    :key="tf.value" 
                                    :class="{ active: item.selectedTimeframe === tf.value }"
                                    @click="updateIndicatorTimeframe(item, tf.value)"
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
                            <Bar v-if="item.chart_type === 'bar'" :data="getEconomicChartData(item)" :options="barChartOptions" />
                            <Line v-else :data="getEconomicChartData(item)" :options="economicChartOptions" />
                        </div>
                        <div v-else class="no-data">
                            <p>No history data available</p>
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
                        Liquidity
                    </button>
                    <button 
                        :class="{ active: activeFedCategory === 'forecasting' }"
                        @click="activeFedCategory = 'forecasting'"
                    >
                        Forecasting
                    </button>
                </div>

                <div v-if="fedLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Fed Data...</p>
                </div>
                <div v-else-if="fedError" class="error-state">
                    <p class="error-message">{{ fedError }}</p>
                </div>
                <div v-else class="fed-data">
                    <!-- Liquidity Section -->
                    <div v-if="activeFedCategory === 'liquidity'" class="category-section">
                        <!-- Balance Sheet / QT -->
                        <div class="liquidity-subsection">
                            <h4 class="subsection-title">Balance Sheet / QT</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>Indicators</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>URL</th>
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
                            <h4 class="subsection-title">Money Market Plumbing</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>Indicators</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>URL</th>
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
                            <h4 class="subsection-title">Stress / Funding</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>Indicators</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>URL</th>
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
                            <h4 class="subsection-title">Yield Curve (Market-Implied Rate Path)</h4>
                            <table class="liquidity-table">
                <thead>
                    <tr>
                                        <th>Indicators</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>URL</th>
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
                            <h4 class="subsection-title">Fed Policy / Forward Guidance</h4>
                            <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>Indicators</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>URL</th>
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
                            <h4 class="subsection-title">FedWatch Tool</h4>
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
                                        <p>No history data available</p>
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
                        <p>Loading Currency Data...</p>
                    </div>
                    <div v-else-if="currencyError" class="error-state">
                        <p class="error-message">{{ currencyError }}</p>
                    </div>
                    <div v-else class="indicators">
                        <div v-for="item in currencyIndicators" :key="item.indicator" class="indicator-card">
                            <div class="card-content">
                                <h3>{{ item.indicator }}</h3>
                                <p class="value">{{ item.value ? item.value.toFixed(4) : 'N/A' }}</p>
                                <p class="date">{{ item.date }}</p>
                                <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                
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
                                <p>No history data available</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Commodity Tab Content -->
            <div v-if="activeTab === 'commodity'" class="tab-content commodity-tab-content">
                <div class="category-tabs">
                    <button 
                        :class="{ active: activeCommodityCategory === 'metals' }"
                        @click="activeCommodityCategory = 'metals'"
                    >
                        Metals
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'agricultural' }"
                        @click="activeCommodityCategory = 'agricultural'"
                    >
                        Agricultural
                    </button>
                    <button 
                        :class="{ active: activeCommodityCategory === 'industrial' }"
                        @click="activeCommodityCategory = 'industrial'"
                    >
                        Industrial
                    </button>
                </div>

                <div class="commodity-data">
                    <div v-if="commodityLoading" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>Loading Commodity Data...</p>
                    </div>
                    <div v-else-if="commodityError" class="error-state">
                        <p class="error-message">{{ commodityError }}</p>
                    </div>
                    <div v-else>
                        <!-- Metals Section -->
                        <div v-if="activeCommodityCategory === 'metals'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.metals" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                        
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
                                        <p>No history data available</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Agricultural Section -->
                        <div v-if="activeCommodityCategory === 'agricultural'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.agricultural" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                        
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
                                        <p>No history data available</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Industrial Section -->
                        <div v-if="activeCommodityCategory === 'industrial'" class="category-section">
                            <div class="indicators">
                                <div v-for="item in commodityIndicators.industrial" :key="item.indicator" class="indicator-card">
                                    <div class="card-content">
                                        <h3>{{ item.indicator }}</h3>
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
                                        <p class="date">{{ item.date }}</p>
                                        <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                        
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
                                        <p>No history data available</p>
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
                    <h4 class="subsection-title">White House Policy Sources</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>Resource</th>
                                        <th>Name</th>
                                        <th>URL</th>
                                        <th>Type</th>
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
                    <h4 class="subsection-title">Federal Register</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>Resource</th>
                                        <th>Name</th>
                                        <th>URL</th>
                                        <th>Type</th>
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
                    <h4 class="subsection-title">Congress Policy Sources</h4>
                    <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>Resource</th>
                                        <th>Name</th>
                                        <th>URL</th>
                                        <th>Type</th>
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

            <!-- Short Interest Tab Content -->
            <div v-if="activeTab === 'short-interest'" class="tab-content short-interest-tab-content">
                <div class="short-interest-category-tabs">
                    <button 
                        v-for="category in shortInterestCategories" 
                        :key="category.value" 
                        :class="{ active: activeShortInterestCategory === category.value }"
                        @click="activeShortInterestCategory = category.value; shortInterestCurrentPage = 1; fetchShortInterestData(1)"
                    >
                        {{ category.label }}
                    </button>
                </div>

                <div v-if="shortInterestLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading short interest data...</p>
                </div>

                <div v-else-if="shortInterestError" class="error-state">
                    <p class="error-message">{{ shortInterestError }}</p>
                    <button @click="fetchShortInterestData" class="retry-btn">Retry</button>
                </div>

                <div v-else class="short-interest-content-section">
                    <div class="short-interest-table-container">
                        <table class="short-interest-table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Current Short Int.</th>
                                    <th>Previous Short Int.</th>
                                    <th>Short Int. Change</th>
                                    <th>Short Int. % Change</th>
                                    <th>Days to Cover</th>
                                    <th>Shares Short Value</th>
                                    <th>Avg Daily Volume</th>
                                    <th>Market Cap</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(row, index) in shortInterestTableData" :key="index">
                                    <td class="symbol-cell">
                                        <strong>{{ row.symbol }}</strong>
                                    </td>
                                    <td>{{ formatShortInterestPercentage(row.current_short_int) }}</td>
                                    <td>{{ formatShortInterestPercentage(row.previous_short_int) }}</td>
                                    <td>{{ formatShortInterestNumber(row.short_int_change) }}</td>
                                    <td :class="getShortInterestChangeClass(row.short_int_pct_change)">
                                        {{ formatShortInterestPercentage(row.short_int_pct_change) }}
                                    </td>
                                    <td>{{ formatShortInterestNumber(row.days_to_cover) }}</td>
                                    <td>{{ row.shares_short_value || '-' }}</td>
                                    <td>{{ row.avg_daily_volume || '-' }}</td>
                                    <td>{{ row.market_cap || '-' }}</td>
                                </tr>
                                <tr v-if="shortInterestTableData.length === 0">
                                    <td colspan="9" class="no-data">No data available</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination Controls -->
                    <div v-if="shortInterestTotalPages > 1" class="short-interest-pagination-container">
                        <div class="short-interest-pagination">
                            <button 
                                @click="goToShortInterestPage(shortInterestCurrentPage - 1)" 
                                :disabled="shortInterestCurrentPage === 1"
                                class="short-interest-pagination-btn"
                            >
                                &lt;
                            </button>
                            
                            <template v-for="pageNum in shortInterestVisiblePages" :key="pageNum">
                                <button
                                    v-if="pageNum !== '...'"
                                    @click="goToShortInterestPage(pageNum)"
                                    :class="{ active: shortInterestCurrentPage === pageNum }"
                                    class="short-interest-pagination-btn short-interest-page-number"
                                >
                                    {{ pageNum }}
                                </button>
                                <span v-else class="short-interest-pagination-ellipsis">...</span>
                            </template>
                            
                            <button 
                                @click="goToShortInterestPage(shortInterestCurrentPage + 1)" 
                                :disabled="shortInterestCurrentPage === shortInterestTotalPages"
                                class="short-interest-pagination-btn"
                            >
                                &gt;
                            </button>
                        </div>
                        
                        <div class="short-interest-pagination-info">
                            <span>100 / page</span>
                        </div>
                    </div>

                    <div v-if="shortInterestUpdatedAt" class="short-interest-data-footer">
                        <p class="short-interest-update-time">Last updated: {{ formatShortInterestDate(shortInterestUpdatedAt) }}</p>
                    </div>
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
                                        <p class="value">{{ item.value ? item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A' }}</p>
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
                                        <p>No history data available</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Energy Tab Content -->
            <div v-if="activeTab === 'energy'" class="tab-content energy-tab-content">
                <div v-if="energyLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Energy Data...</p>
                </div>
                <div v-else-if="energyError" class="error-state">
                    <p class="error-message">{{ energyError }}</p>
                </div>
                <div v-else class="energy-layout">
                    <!-- Main Content Area -->
                    <div class="main-content">
                        <!-- Energy Prices (Line) -->
                        <div class="card full-width">
                            <h3>Energy Prices</h3>
                            
                            <div class="timeframe-selector">
                                <button 
                                    v-for="tf in priceTimeframes" 
                                    :key="tf.value" 
                                    :class="{ active: selectedPriceTimeframe === tf.value }"
                                    @click="changePriceTimeframe(tf.value)"
                                >
                                    {{ tf.label }}
                                </button>
                            </div>

                            <div class="chart-container">
                                <Line :data="priceData" :options="priceChartOptions" />
                            </div>
                        </div>

                        <!-- Energy Data Sources Table -->
                        <div class="card">
                            <h3>Energy Data Sources</h3>
                            <table class="liquidity-table">
                                <thead>
                                    <tr>
                                        <th>Source ID</th>
                                        <th>Description</th>
                                        <th>URL</th>
                                        <th>Data Type / Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Nuclear regulatory commission</td>
                                        <td>NRC public document & docket search (ADAMS) — used to check case status for applications like Oklo</td>
                                        <td><a href="https://adams-search.nrc.gov/" target="_blank" rel="noopener noreferrer">https://adams-search.nrc.gov/</a></td>
                                        <td>Regulatory / licensing case status</td>
                                    </tr>
                                    <tr>
                                        <td>EIA electricity data</td>
                                        <td>U.S. electricity generation, consumption, retail sales, price, capacity (all sectors)</td>
                                        <td><a href="https://www.eia.gov/electricity/data/browser/" target="_blank" rel="noopener noreferrer">https://www.eia.gov/electricity/data/browser/</a></td>
                                        <td>Electricity generation & consumption (all sectors)</td>
                                    </tr>
                                    <tr>
                                        <td>EIA electric power monthly</td>
                                        <td>Detailed monthly generation mix, consumption by sector, prices, fuel mix</td>
                                        <td><a href="https://www.eia.gov/electricity/monthly/" target="_blank" rel="noopener noreferrer">https://www.eia.gov/electricity/monthly/</a></td>
                                        <td>Generation mix, consumption, sector breakdown</td>
                                    </tr>
                                    <tr>
                                        <td>U.S. electricity supply & generation</td>
                                        <td>Aggregated U.S. electricity supply & generation metadata (private dataset)</td>
                                        <td><a href="https://www.gridinfo.com/united-states" target="_blank" rel="noopener noreferrer">https://www.gridinfo.com/united-states</a></td>
                                        <td>Supplementary electricity supply data</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Right Sidebar -->
                    <div class="sidebar">
                        <!-- Generation Mix (Doughnut) -->
                        <div class="card">
                            <h3>Generation by Fuel Type</h3>
                            <div class="chart-container">
                                <Doughnut :data="generationData" :options="pieOptions" />
                            </div>
                        </div>

                        <!-- Consumption by Sector (Pie) -->
                        <div class="card">
                            <h3>Consumption by Sector</h3>
                            <div class="chart-container">
                                <Pie :data="consumptionData" :options="pieOptions" />
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
import { ref, onMounted, computed, watch } from 'vue';
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
import { getDailyCache, setDailyCache, clearCacheByKey } from '../utils/dailyCache.js'

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

// Bond Tab State
const bondData = ref({
  treasury_yields: [],
  yield_curve: [],
  tips_breakeven: [],
  central_bank_rates: [],
  credit_spreads: [],
  funding_stress: []
});
const bondLoading = ref(false);
const bondError = ref(null);
const activeBondCategory = ref('treasury_yields');

const bondTimeframes = [
  { label: '1M', value: 'daily' },
  { label: '3M', value: 'weekly' },
  { label: '1Y', value: 'monthly' },
  { label: '5Y', value: 'yearly' },
  { label: 'Max', value: 'max' }
];

const bondCategories = [
  { label: 'Treasury Yields', value: 'treasury_yields' },
  { label: 'Yield Curve', value: 'yield_curve' },
  { label: 'TIPS & Breakeven', value: 'tips_breakeven' },
  { label: 'Central Bank Rates', value: 'central_bank_rates' },
  { label: 'Credit Spreads', value: 'credit_spreads' },
  { label: 'Funding Stress', value: 'funding_stress' }
];

// Economic Tab State (from MacroView)
const economicIndicators = ref([]);
const economicLoading = ref(false);
const economicError = ref(null);
const economicTimeframes = [
    { label: '1M', value: 'monthly' },
    { label: '3M', value: 'quarterly' },
    { label: '1Y', value: 'yearly' },
    { label: '5Y', value: '5y' }
];

// Fed Tab State
const fedIndicators = ref([]);
const fedLoading = ref(false);
const fedError = ref(null);
const activeFedCategory = ref('forecasting');
const fedTimeframes = [
    { label: '1M', value: 'monthly' },
    { label: '3M', value: 'quarterly' },
    { label: '1Y', value: 'yearly' },
    { label: '5Y', value: '5y' }
];

// Currency Tab State
const currencyIndicators = ref([]);
const currencyLoading = ref(false);
const currencyError = ref(null);
const currencyTimeframes = [
  { label: '1M', value: 'monthly' },
  { label: '3M', value: 'quarterly' },
  { label: '1Y', value: 'yearly' },
  { label: '5Y', value: '5y' }
];

// Commodity Tab State
const activeCommodityCategory = ref('metals');
const commodityIndicators = ref({
  metals: [],
  agricultural: [],
  industrial: []
});
const commodityLoading = ref(false);
const commodityError = ref(null);
const commodityTimeframes = [
  { label: '1M', value: 'monthly' },
  { label: '3M', value: 'quarterly' },
  { label: '1Y', value: 'yearly' },
  { label: '5Y', value: '5y' }
];

// Commodity series mapping by category
const commoditySeriesMap = {
  metals: ['GOLDAMGBD228NLBM', 'PCOPPUSDM', 'PIORECRUSDM', 'PLATINUM', 'PSILICON'],
  agricultural: ['PSOYBUSDM', 'PCOFFUSDM', 'PSUGAR', 'PCORNUSDM'],
  industrial: ['PZINC', 'PALUMINUM']
};

// Crypto Tab State
const cryptoIndicators = ref([]);
const cryptoLoading = ref(false);
const cryptoError = ref(null);
const cryptoTimeframes = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Yearly', value: 'yearly' }
];

// Bond cache configuration
const BOND_CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const BOND_CACHE_KEY_PREFIX = 'bond_series_';

const getBondCacheKey = (seriesId, timeframe) => `${BOND_CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

const getBondCachedData = (seriesId, timeframe) => {
    try {
        const key = getBondCacheKey(seriesId, timeframe);
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < BOND_CACHE_EXPIRATION) {
            return data;
        }
        localStorage.removeItem(key);
        return null;
    } catch (e) {
        return null;
    }
};

const setBondCachedData = (seriesId, timeframe, data) => {
    try {
        const key = getBondCacheKey(seriesId, timeframe);
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.error('Cache write error', e);
    }
};

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

// Short Interest Tab State
const activeShortInterestCategory = ref('most-shorted');
const shortInterestLoading = ref(false);
const shortInterestError = ref(null);
const shortInterestTableData = ref([]);
const shortInterestUpdatedAt = ref(null);
const shortInterestCurrentPage = ref(1);
const shortInterestTotalPages = ref(20); // Maximum 20 pages as per backend
const shortInterestItemsPerPage = 100;

const shortInterestCategories = [
  { label: 'Most Shorted', value: 'most-shorted' },
  { label: 'Largest Increase', value: 'largest-increase' },
  { label: 'Largest Decrease', value: 'largest-decrease' }
];

const shortInterestVisiblePages = computed(() => {
  const pages = [];
  const maxVisible = 7; // Show up to 7 page numbers
  
  if (shortInterestTotalPages.value <= maxVisible) {
    // Show all pages if total is less than max visible
    for (let i = 1; i <= shortInterestTotalPages.value; i++) {
      pages.push(i);
    }
  } else {
    // Show first page
    pages.push(1);
    
    if (shortInterestCurrentPage.value <= 3) {
      // Near the beginning
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(shortInterestTotalPages.value);
    } else if (shortInterestCurrentPage.value >= shortInterestTotalPages.value - 2) {
      // Near the end
      pages.push('...');
      for (let i = shortInterestTotalPages.value - 4; i <= shortInterestTotalPages.value; i++) {
        pages.push(i);
      }
    } else {
      // In the middle
      pages.push('...');
      for (let i = shortInterestCurrentPage.value - 1; i <= shortInterestCurrentPage.value + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(shortInterestTotalPages.value);
    }
  }
  
  return pages;
});

const fetchShortInterestData = async (page = null) => {
  shortInterestLoading.value = true;
  shortInterestError.value = null;
  
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      shortInterestError.value = 'Please login to view short interest data';
      shortInterestLoading.value = false;
      return;
    }

    let endpoint = '';
    switch (activeShortInterestCategory.value) {
      case 'most-shorted':
        endpoint = 'http://localhost:8000/api/short-interest/most-shorted';
        break;
      case 'largest-increase':
        endpoint = 'http://localhost:8000/api/short-interest/largest-increase';
        break;
      case 'largest-decrease':
        endpoint = 'http://localhost:8000/api/short-interest/largest-decrease';
        break;
      default:
        endpoint = 'http://localhost:8000/api/short-interest/most-shorted';
    }

    // Add page parameter if specified
    const pageToFetch = page !== null ? page : shortInterestCurrentPage.value;
    const url = pageToFetch ? `${endpoint}?page=${pageToFetch}` : endpoint;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch data' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    shortInterestTableData.value = data.data || [];
    shortInterestUpdatedAt.value = data.updated_at || null;
    
    // If we got less than itemsPerPage, we've reached the last page
    if (shortInterestTableData.value.length < shortInterestItemsPerPage && pageToFetch < shortInterestTotalPages.value) {
      shortInterestTotalPages.value = pageToFetch;
    }
  } catch (err) {
    console.error('Error fetching short interest data:', err);
    shortInterestError.value = err.message || 'Failed to load short interest data';
    shortInterestTableData.value = [];
  } finally {
    shortInterestLoading.value = false;
  }
};

const goToShortInterestPage = (page) => {
  if (page < 1 || page > shortInterestTotalPages.value || page === shortInterestCurrentPage.value) {
    return;
  }
  shortInterestCurrentPage.value = page;
  fetchShortInterestData(page);
};

const formatShortInterestPercentage = (value) => {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(2)}%`;
};

const formatShortInterestNumber = (value) => {
  if (value === null || value === undefined) return '-';
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}K`;
  }
  return value.toFixed(2);
};

const getShortInterestChangeClass = (value) => {
  if (value === null || value === undefined) return '';
  if (value > 0) return 'positive-change';
  if (value < 0) return 'negative-change';
  return '';
};

const formatShortInterestDate = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
};

// Energy Tab State (from EnergyView)
const energyLoading = ref(true);
const energyError = ref(null);
const generation = ref([]);
const consumption = ref([]);
const gridData = ref({});
const prices = ref([]);

const selectedEnergyTimeframe = ref('realtime');
const energyTimeframes = [
    { label: 'Real-time', value: 'realtime' },
    { label: 'Days', value: 'days' },
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: '5 Years', value: '5y' }
];

const selectedPriceTimeframe = ref('days');
const priceTimeframes = [
    { label: 'Days', value: 'days' },
    { label: 'Weekly', value: 'weekly' },
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: '5 Years', value: '5y' }
];

// Market indices data
const indices = ref([
    { name: 'Dow Jones', value: 0, change: 0, history: [] },
    { name: 'NASDAQ', value: 0, change: 0, history: [] },
    { name: 'S&P 500', value: 0, change: 0, history: [] },
    { name: 'Russell 2000', value: 0, change: 0, history: [] }
]);

const miniChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { 
      enabled: true,
      mode: 'index',
      intersect: false
    }
  },
  scales: {
    x: { 
      display: true,
      grid: { color: 'rgba(0, 0, 0, 0.1)' },
      ticks: { 
        color: '#666666',
        font: { size: 9 },
        maxTicksLimit: 5
      }
    },
    y: { 
      display: true,
      grid: { color: 'rgba(0, 0, 0, 0.1)' },
      ticks: { 
        color: '#666666',
        font: { size: 9 },
        callback: function(value) {
          return value.toLocaleString();
        }
      }
    }
  },
  elements: {
    point: { radius: 0, hitRadius: 10, hoverRadius: 4 },
    line: { borderWidth: 2, tension: 0.3 }
  }
};

const fetchIndices = async () => {
    // Check cache first
    const cached = getDailyCache('indices_data');
    if (cached) {
        console.log('Using cached indices data');
        indices.value = cached;
        return;
    }
    
    // Fetch fresh data if no cache
    try {
        const response = await fetch('http://localhost:8000/api/internal/indices');
        if (!response.ok) throw new Error('Failed to fetch indices');
        const data = await response.json();
        indices.value = data;
        
        // Cache the data
        setDailyCache('indices_data', data);
    } catch (e) {
        console.error('Error fetching indices:', e);
    }
};

const updateIndices = async () => {
    clearCacheByKey('indices_data');
    await fetchIndices();
};

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

const updateData = async () => {
    // Set loading states for all sections
    loading.value = true;
    bondLoading.value = true;
    economicLoading.value = true;
    fedLoading.value = true;
    energyLoading.value = true;
    currencyLoading.value = true;
    commodityLoading.value = true;
    cryptoLoading.value = true;
    
    // Clear all daily caches
    clearCacheByKey('indices_data');
    clearCacheByKey('bond_data_monthly');
    clearCacheByKey('macro_data_monthly');
    clearCacheByKey('fed_data_monthly');
    clearCacheByKey('energy_generation');
    clearCacheByKey('energy_consumption');
    clearCacheByKey('crypto_data_daily');
    clearCacheByKey('commodity_data_monthly');
    clearCacheByKey('currency_data_monthly');
    
    // Clear all per-item timeframe caches (localStorage)
    clearAllTimeframeCaches();
    
    // Update all sections in parallel
    try {
        await Promise.all([
            updateIndices(),
            updateBondData(),
            updateEconomicData(),
            updateFedData(),
            updateEnergyData(),
            updateCommodityData(),
            updateCurrencyData(),
            updateCryptoData()
        ]);
    } catch (error) {
        console.error('Error updating data:', error);
    } finally {
        // Reset main loading state
        loading.value = false;
    }
};


const getIndexChartData = (index) => {
    if (!index.history || index.history.length === 0) {
        return {
            labels: [],
            datasets: [{
                borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
                data: [],
                fill: false
            }]
        };
    }
    
    return {
        labels: index.history.map(item => {
            const date = new Date(item.date);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        }),
        datasets: [{
            borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
            data: index.history.map(item => item.value),
            fill: false
        }]
    };
};

// Bond Chart Options
const bondChartOptions = {
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

const getBondChartData = (item) => {
  const sortedHistory = [...(item.history || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  return {
    labels: sortedHistory.map(h => h.date),
    datasets: [
      {
        label: item.title,
        backgroundColor: '#42b983',
        borderColor: '#42b983',
        data: sortedHistory.map(h => h.value),
        fill: false
      }
    ]
  }
}

const fetchBondData = async () => {
  bondLoading.value = true;
  bondError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('bond_data_monthly');
  if (cached) {
    console.log('Using cached bond data');
    bondData.value = cached;
    bondLoading.value = false;
    return;
  }
  
  try {
    // Initial fetch of all data with default 'monthly' (1Y) timeframe
    const response = await fetch(`http://localhost:8000/api/bond/all?timeframe=monthly`);
    if (!response.ok) throw new Error('Failed to fetch bond data');
            const data = await response.json();
    
    // Initialize with default timeframe state for each item in each category
    Object.keys(data).forEach(category => {
        data[category] = data[category].map(item => ({
            ...item,
            selectedTimeframe: 'monthly',
            loading: false
        }));
    });
    
    bondData.value = data;
    
    // Cache the data
    setDailyCache('bond_data_monthly', data);
    
  } catch (err) {
    bondError.value = err.message;
  } finally {
    bondLoading.value = false;
  }
};

const updateBondData = async () => {
  clearCacheByKey('bond_data_monthly');
  await fetchBondData();
};

const updateBondItemTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getBondCachedData(item.series_id, timeframe);
    if (cached) {
        Object.assign(item, cached);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        item.loading = false;
        return;
    }

    try {
        const response = await fetch(`http://localhost:8000/api/bond/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch series');
        const data = await response.json();
        
        // Update item properties with new data
        Object.assign(item, data);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        
        setBondCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.title}:`, err);
    } finally {
        item.loading = false;
    }
};

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

const priceData = computed(() => ({
    labels: prices.value.map(i => i.date),
    datasets: [
        {
            label: 'Oil Price ($)',
            data: prices.value.map(i => i.oil),
            borderColor: '#e74c3c',
            backgroundColor: '#e74c3c',
            tension: 0.1,
            yAxisID: 'y'
        },
        {
            label: 'Natural Gas ($)',
            data: prices.value.map(i => i.gas),
            borderColor: '#f1c40f',
            backgroundColor: '#f1c40f',
            tension: 0.1,
            yAxisID: 'y1'
        }
    ]
}));

const priceChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
      y: { 
          type: 'linear',
          display: true,
          position: 'left',
          ticks: { color: '#e74c3c' }, 
          grid: { color: 'rgba(0, 0, 0, 0.1)' },
          title: { display: true, text: 'Oil ($)', color: '#e74c3c' }
      },
      y1: {
          type: 'linear',
          display: true,
          position: 'right',
          ticks: { color: '#f1c40f' },
          grid: { drawOnChartArea: false },
          title: { display: true, text: 'Gas ($)', color: '#f1c40f' }
      },
      x: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } }
  },
  plugins: {
      legend: { labels: { color: '#000000' } }
  }
}));

const fetchGridData = async (timeframe) => {
    try {
        const res = await fetch(`http://localhost:8000/api/energy/grid?timeframe=${timeframe}`);
        if (!res.ok) throw new Error("Failed to fetch grid data");
        gridData.value = await res.json();
    } catch (err) {
        console.error(err);
    }
};

const fetchPriceData = async (timeframe) => {
    try {
        const res = await fetch(`http://localhost:8000/api/energy/prices?timeframe=${timeframe}`);
        if (!res.ok) throw new Error("Failed to fetch price data");
        prices.value = await res.json();
    } catch (err) {
        console.error(err);
    }
};

const changeEnergyTimeframe = (timeframe) => {
    selectedEnergyTimeframe.value = timeframe;
    fetchGridData(timeframe);
};

const changePriceTimeframe = (timeframe) => {
    selectedPriceTimeframe.value = timeframe;
    fetchPriceData(timeframe);
};

const fetchEnergyData = async () => {
    // Check daily cache first
    const cachedGeneration = getDailyCache('energy_generation');
    const cachedConsumption = getDailyCache('energy_consumption');
    
    if (cachedGeneration && cachedConsumption) {
        console.log('Using cached energy data');
        generation.value = cachedGeneration;
        consumption.value = cachedConsumption;
        
        // Still fetch grid and price data with their timeframes
        await fetchGridData(selectedEnergyTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);
        
        energyLoading.value = false;
        return;
    }
    
    try {
        const [genRes, conRes] = await Promise.all([
            fetch('http://localhost:8000/api/energy/generation'),
            fetch('http://localhost:8000/api/energy/consumption')
        ]);

        if (!genRes.ok || !conRes.ok) throw new Error("Failed to fetch energy data");

        const genData = await genRes.json();
        const conData = await conRes.json();
        
        generation.value = genData;
        consumption.value = conData;
        
        // Cache the data
        setDailyCache('energy_generation', genData);
        setDailyCache('energy_consumption', conData);
        
        // Fetch initial data
        await fetchGridData(selectedEnergyTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);

    } catch (err) {
        energyError.value = err.message;
    } finally {
        energyLoading.value = false;
    }
};

const updateEnergyData = async () => {
    clearCacheByKey('energy_generation');
    clearCacheByKey('energy_consumption');
    await fetchEnergyData();
};

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
    const response = await fetch(`http://localhost:8000/api/internal/macro?timeframe=monthly`);
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
    const response = await fetch(`http://localhost:8000/api/internal/macro?timeframe=monthly`);
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
  const cached = getDailyCache('currency_data_monthly');
  if (cached) {
    console.log('Using cached currency data');
    // Ensure history is preserved from cache (like Bond/Economic tabs)
    const processedCached = cached.map(item => ({
      ...item,
      history: item.history || [], // Ensure history is always an array
      selectedTimeframe: item.selectedTimeframe || 'monthly',
      loading: false
    }));
    
    currencyIndicators.value = processedCached;
    currencyLoading.value = false;
    return;
  }
  
  try {
    // Fetch currency series
    const currencySeries = ['DEXUSEU', 'DEXJPUS', 'DEXCHUS'];
    const promises = currencySeries.map(seriesId => 
      fetch(`http://localhost:8000/api/internal/macro/series/${seriesId}?timeframe=monthly`)
        .then(res => res.json())
    );
    
    const data = await Promise.all(promises);
    
    // Initialize with default timeframe state and ensure history is always an array
    const processedData = data.map(item => ({
      ...item,
      history: item.history || [], // Ensure history is always an array
      selectedTimeframe: 'monthly',
      loading: false
    }));
    
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
    const response = await fetch(`http://localhost:8000/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
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
  const cached = getDailyCache('commodity_data_monthly');
  if (cached) {
    console.log('Using cached commodity data');
    // Filter out removed commodities from cached data and check if all required series are present
    const filteredCached = {};
    let cacheComplete = true;
    
    Object.keys(commoditySeriesMap).forEach(category => {
      const allowedSeriesIds = new Set(commoditySeriesMap[category]);
      const cachedItems = (cached[category] || []).filter(item => 
        allowedSeriesIds.has(item.series_id)
      );
      
      // Check if all required series are in cache
      const cachedSeriesIds = new Set(cachedItems.map(item => item.series_id));
      const missingSeries = commoditySeriesMap[category].filter(id => !cachedSeriesIds.has(id));
      
      if (missingSeries.length > 0) {
        console.log(`Missing series in cache for ${category}:`, missingSeries);
        cacheComplete = false;
      }
      
      filteredCached[category] = cachedItems;
    });
    
    // If cache is complete, use it; otherwise fetch fresh data
    if (cacheComplete) {
      commodityIndicators.value = filteredCached;
      commodityLoading.value = false;
      return;
    } else {
      console.log('Cache incomplete, fetching fresh data');
      // Clear cache to force fresh fetch
      clearCacheByKey('commodity_data_monthly');
    }
  }
  
  try {
    // Fetch all commodity series by category
    const allPromises = {};
    
    for (const [category, seriesList] of Object.entries(commoditySeriesMap)) {
      allPromises[category] = Promise.all(
        seriesList.map(seriesId => 
          fetch(`http://localhost:8000/api/internal/macro/series/${seriesId}?timeframe=monthly`)
            .then(res => res.json())
        )
      );
    }
    
    const results = await Promise.all(Object.values(allPromises));
    const categories = Object.keys(commoditySeriesMap);
    
    // Process data for each category
    const processedData = {};
    categories.forEach((category, index) => {
      processedData[category] = results[index].map(item => ({
        ...item,
        selectedTimeframe: 'monthly',
        loading: false
      }));
    });
    
    commodityIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('commodity_data_monthly', processedData);
    
  } catch (err) {
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
    const response = await fetch(`http://localhost:8000/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
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
    const response = await fetch('http://localhost:8000/api/internal/crypto/all?timeframe=daily');
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
    const historyResponse = await fetch(`http://localhost:8000/api/internal/crypto/${item.series_id}/history?period=${timeframe}`);
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
        const response = await fetch(`http://localhost:8000/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
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
        const response = await fetch(`http://localhost:8000/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
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
watch(activeTab, (newTab) => {
  if (newTab === 'short-interest' && shortInterestTableData.value.length === 0) {
    fetchShortInterestData();
  }
});

onMounted(() => {
    fetchIndices();
    
    // Fetch bond data when bond tab might be accessed
    fetchBondData();
    
    // Fetch economic data when economic tab might be accessed
    fetchEconomicData();
    
    // Fetch Fed data when Fed tab might be accessed
    fetchFedData();
    
    // Fetch energy data when energy tab might be accessed
    fetchEnergyData();
    
    // Fetch currency data when currency tab might be accessed
    fetchCurrencyData();
    
    // Fetch commodity data when commodity tab might be accessed
    fetchCommodityData();
    
    // Fetch crypto data when crypto tab might be accessed
    fetchCryptoData();
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
.short-interest-tab-content {
    padding: 0;
}

.short-interest-category-tabs {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    border-bottom: 2px solid #e5e5e5;
}

.short-interest-category-tabs button {
    padding: 0.75rem 1.5rem;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: #666666;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: -2px;
}

.short-interest-category-tabs button:hover {
    color: #000000;
    background: rgba(0, 0, 0, 0.02);
}

.short-interest-category-tabs button.active {
    color: #3498db;
    border-bottom-color: #3498db;
    font-weight: 600;
}

.short-interest-content-section {
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 1.5rem;
    overflow-x: auto;
}

.short-interest-table-container {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 600px;
    width: 100%;
    position: relative;
}

.short-interest-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.short-interest-table thead {
    background-color: #f8f9fa;
    border-bottom: 2px solid #e5e5e5;
    position: sticky;
    top: 0;
    z-index: 10;
}

.short-interest-table th {
    padding: 1rem 0.75rem;
    text-align: left;
    font-weight: 600;
    color: #000000;
    white-space: nowrap;
    border-right: 1px solid #e5e5e5;
}

.short-interest-table th:last-child {
    border-right: none;
}

.short-interest-table tbody tr {
    border-bottom: 1px solid #e5e5e5;
    transition: background-color 0.15s ease;
}

.short-interest-table tbody tr:hover {
    background-color: #f8f9fa;
}

.short-interest-table td {
    padding: 0.875rem 0.75rem;
    color: #000000;
    border-right: 1px solid #e5e5e5;
    white-space: nowrap;
}

.short-interest-table td:last-child {
    border-right: none;
}

.short-interest-table .symbol-cell {
    font-weight: 600;
}

.short-interest-table .positive-change {
    color: #e74c3c;
    font-weight: 500;
}

.short-interest-table .negative-change {
    color: #27ae60;
    font-weight: 500;
}

.short-interest-table .no-data {
    text-align: center;
    padding: 2rem;
    color: #666666;
    font-style: italic;
}

.short-interest-data-footer {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e5e5;
    text-align: center;
    color: #666666;
    font-size: 0.9rem;
}

.short-interest-update-time {
    font-size: 0.85rem;
    color: #999999;
}

.short-interest-pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e5e5;
}

.short-interest-pagination {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.short-interest-pagination-btn {
    padding: 0.5rem 0.75rem;
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 4px;
    color: #000000;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.short-interest-pagination-btn:hover:not(:disabled) {
    background: #f8f9fa;
    border-color: #3498db;
    color: #3498db;
}

.short-interest-pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.short-interest-pagination-btn.active {
    background: #3498db;
    border-color: #3498db;
    color: #ffffff;
    font-weight: 600;
}

.short-interest-pagination-btn.active:hover {
    background: #2980b9;
    border-color: #2980b9;
}

.short-interest-pagination-ellipsis {
    padding: 0 0.5rem;
    color: #666666;
    font-size: 0.9rem;
}

.short-interest-pagination-info {
    color: #666666;
    font-size: 0.9rem;
}
</style>
