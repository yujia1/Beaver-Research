<template>
  <div class="language-switcher">
    <button 
      class="lang-btn" 
      @click="toggleLanguage"
      :title="currentLocale === 'en' ? 'Switch to Chinese' : 'Switch to English'"
    >
      <span class="lang-text">{{ currentLocale === 'en' ? 'EN' : '中' }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const currentLocale = computed(() => locale.value)

const toggleLanguage = () => {
  const newLocale = locale.value === 'en' ? 'zh' : 'en'
  locale.value = newLocale
  localStorage.setItem('user-locale', newLocale)
}
</script>

<style scoped>
.language-switcher {
  display: flex;
  align-items: center;
}

.lang-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s ease;
  min-width: 40px;
  display: flex;
  justify-content: center;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
}
</style>
