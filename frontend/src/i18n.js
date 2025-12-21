import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'

// Get saved locale from local storage or default to English
const savedLocale = localStorage.getItem('user-locale') || 'en'

const i18n = createI18n({
    legacy: false, // Use Composition API
    locale: savedLocale,
    fallbackLocale: 'en',
    globalInjection: true, // Inject $t globally
    messages: {
        en,
        zh
    }
})

export default i18n
