<template>
  <div class="market-news-container">
    <div class="news-header">
      <div class="title-container">
        <h3>{{ t('dashboard.market_news.title') }}</h3>
        <span class="pulse-dot"></span>
      </div>
      <div class="header-actions">
        <div class="search-container">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="text" :placeholder="t('market_news.search_placeholder')" class="search-input" />
        </div>
      </div>
    </div>

    <div class="news-list">
      <div v-for="item in newsItems" :key="item.id" class="news-item" @click="openNews(item.url)">
        <div class="news-meta">
          <span class="news-time">{{ item.time }}</span>
          <div class="news-trending" :class="item.sentiment">
            <svg v-if="item.sentiment === 'positive'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
          </div>
        </div>

        <div class="news-content">
          <div class="news-tags">
            <span v-for="tag in item.tags" :key="tag" class="news-tag">{{ tag }}</span>
          </div>
          <h4 class="news-headline">{{ item.headline }}</h4>
          <p class="news-summary">{{ item.summary }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import API_BASE_URL from '@/config/api.js';

const { t } = useI18n();
const newsItems = ref([]);

const formatTime = (dateString) => {
    try {
        const date = new Date(dateString);
        // Format to "05:50:10 PM" style
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    } catch (e) {
        return dateString;
    }
};

const fetchNews = async () => {
    try {
        // Use the configured API base URL (handling https if needed via config logic)
        // Note: API_BASE_URL usually doesn't end with slash
        const response = await fetch(`${API_BASE_URL}/api/alphatrade/market-news-feed`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        newsItems.value = data.map(item => ({
            ...item,
            time: formatTime(item.time)
        }));
    } catch (e) {
        console.error("Failed to fetch news", e);
        // Fallback or empty state could be handled here
    }
};

onMounted(() => {
    fetchNews();
});

const openNews = (url) => {
    if (url) {
        window.open(url, '_blank');
    }
};
</script>

<style scoped>
.market-news-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
  font-family: 'Inter', sans-serif;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.news-header h3 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #111827;
  text-transform: uppercase;
  margin: 0;
  letter-spacing: 0.5px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #3b82f6;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  50% { transform: scale(1); opacity: 0.7; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0); }
  100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
}

.header-actions {
  display: flex;
  align-items: center;
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #9ca3af;
}

.search-input {
  padding: 6px 10px 6px 32px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #374151;
  width: 200px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.news-list {
  display: flex;
  flex-direction: column;
}

.news-item {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem 0;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background-color 0.2s;
}

.news-item:hover {
  background-color: #f9fafb;
}

.news-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.news-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 80px;
  gap: 0.5rem;
}

.news-time {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  width: 60px;
  line-height: 1.2;
}

.news-trending {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.news-trending.positive {
  background-color: #ecfdf5;
  color: #10b981;
}

.news-trending.negative {
  background-color: #fef2f2;
  color: #ef4444;
}

.news-content {
  flex: 1;
}

.news-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.news-tag {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #f3f4f6;
  color: #4b5563;
  text-transform: uppercase;
}

.news-tag:first-child {
  background-color: #eff6ff;
  color: #2563eb;
}

.news-headline {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.news-summary {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}
</style>
