/**
 * Daily Cache Utility
 * Caches data in localStorage with daily expiration
 */

const CACHE_PREFIX = 'daily_cache_';

/**
 * Get the cache key with today's date
 */
const getCacheKey = (key) => {
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    return `${CACHE_PREFIX}${key}_${today}`;
};

/**
 * Get cached data if it exists and is from today
 */
export const getDailyCache = (key) => {
    try {
        const cacheKey = getCacheKey(key);
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
            return JSON.parse(cached);
        }

        return null;
    } catch (error) {
        console.error('Error reading from cache:', error);
        return null;
    }
};

/**
 * Set data in cache with today's date
 */
export const setDailyCache = (key, data) => {
    try {
        const cacheKey = getCacheKey(key);
        localStorage.setItem(cacheKey, JSON.stringify(data));

        // Clean up old cache entries (older than today)
        cleanOldCache(key);
    } catch (error) {
        console.error('Error writing to cache:', error);
    }
};

/**
 * Clean up cache entries older than today for a given key
 */
const cleanOldCache = (key) => {
    try {
        const today = new Date().toISOString().split('T')[0];
        const keysToRemove = [];

        // Find all cache keys for this data type
        for (let i = 0; i < localStorage.length; i++) {
            const storageKey = localStorage.key(i);
            if (storageKey && storageKey.startsWith(`${CACHE_PREFIX}${key}_`)) {
                // Extract date from key
                const dateStr = storageKey.split('_').pop();
                if (dateStr !== today) {
                    keysToRemove.push(storageKey);
                }
            }
        }

        // Remove old entries
        keysToRemove.forEach(k => localStorage.removeItem(k));
    } catch (error) {
        console.error('Error cleaning cache:', error);
    }
};

/**
 * Clear all daily cache
 */
export const clearDailyCache = () => {
    try {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(CACHE_PREFIX)) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(k => localStorage.removeItem(k));
    } catch (error) {
        console.error('Error clearing cache:', error);
    }
};

/**
 * Clear cache for a specific key
 */
export const clearCacheByKey = (key) => {
    try {
        const cacheKey = getCacheKey(key);
        localStorage.removeItem(cacheKey);
    } catch (error) {
        console.error('Error clearing cache by key:', error);
    }
};
