<template>
  <div class="research-view" :class="viewModeClass">
    <ResearchEditView
      :view-mode="viewMode"
      :active-agent="activeAgent"
      :ticker="ticker"
      @update:view-mode="viewMode = $event"
      @update:active-agent="activeAgent = $event"
      @update:ticker="ticker = $event"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ResearchEditView from './ResearchEditView.vue'

// State Management - Lifted to parent
const viewMode = ref('COMPANY') // 'COMPANY' | 'MARKET'
const activeAgent = ref('FUNDAMENTAL_AGENT')
const ticker = ref('TSLA')

const viewModeClass = computed(() => {
  return viewMode.value === 'COMPANY' ? 'company-mode' : 'market-mode'
})
</script>

<style scoped>
.research-view {
  min-height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
}

/* Theme Colors */
.research-view.company-mode {
  --accent-color: #f59e0b; /* Amber-500 */
  --accent-glow: rgba(245, 158, 11, 0.3);
}

.research-view.market-mode {
  --accent-color: #22d3ee; /* Cyan-400 */
  --accent-glow: rgba(34, 211, 238, 0.3);
}

.research-view {
  background: linear-gradient(135deg, #0c0a09 0%, #1c1917 100%); /* Stone-950/900 */
}
</style>
