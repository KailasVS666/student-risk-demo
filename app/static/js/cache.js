/**
 * Cache Manager Module
 * Implements intelligent caching for API responses and expensive computations.
 */

import APP_CONFIG from './config.js';

// Cache storage
const cache = new Map();

// Cache configuration
const CACHE_CONFIG = {
  PREDICTION_TTL: 5 * 60 * 1000, // 5 minutes
  MAX_CACHE_SIZE: 50,
  CACHE_KEY_PREFIX: 'api_cache_'
};

/**
 * Generates a cache key from request data.
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request data
 * @returns {string} Cache key
 * @private
 */
function generateCacheKey(endpoint, data) {
  const dataString = JSON.stringify(data);
  return `${CACHE_CONFIG.CACHE_KEY_PREFIX}${endpoint}_${dataString}`;
}

/**
 * Checks if cached data is still valid.
 * @param {Object} cachedItem - Cached item with timestamp
 * @param {number} ttl - Time to live in milliseconds
 * @returns {boolean} True if cache is valid
 * @private
 */
function isCacheValid(cachedItem, ttl) {
  if (!cachedItem || !cachedItem.timestamp) return false;
  return Date.now() - cachedItem.timestamp < ttl;
}

/**
 * Evicts oldest cache entries if size exceeds limit.
 * @private
 */
function evictOldestEntries() {
  if (cache.size <= CACHE_CONFIG.MAX_CACHE_SIZE) return;
  
  // Convert to array and sort by timestamp
  const entries = Array.from(cache.entries())
    .sort((a, b) => a[1].timestamp - b[1].timestamp);
  
  // Remove oldest 20% of entries
  const toRemove = Math.ceil(cache.size * 0.2);
  for (let i = 0; i < toRemove; i++) {
    cache.delete(entries[i][0]);
  }
}

/**
 * Caches API response data.
 * @param {string} endpoint - API endpoint
 * @param {Object} requestData - Request data used as part of cache key
 * @param {Object} responseData - Response data to cache
 */
export function setCacheData(endpoint, requestData, responseData) {
  const key = generateCacheKey(endpoint, requestData);
  
  cache.set(key, {
    data: responseData,
    timestamp: Date.now()
  });
  
  evictOldestEntries();
}

/**
 * Retrieves cached API response if valid.
 * @param {string} endpoint - API endpoint
 * @param {Object} requestData - Request data used as part of cache key
 * @param {number} [ttl] - Time to live in milliseconds (default: PREDICTION_TTL)
 * @returns {Object|null} Cached data or null if not found/expired
 */
export function getCacheData(endpoint, requestData, ttl = CACHE_CONFIG.PREDICTION_TTL) {
  const key = generateCacheKey(endpoint, requestData);
  const cachedItem = cache.get(key);
  
  if (isCacheValid(cachedItem, ttl)) {
    return cachedItem.data;
  }
  
  // Remove expired entry
  if (cachedItem) {
    cache.delete(key);
  }
  
  return null;
}

/**
 * Clears all cached data.
 */
export function clearCache() {
  cache.clear();
}

/**
 * Clears cache for specific endpoint.
 * @param {string} endpoint - API endpoint to clear
 */
export function clearEndpointCache(endpoint) {
  const keysToDelete = [];
  
  for (const key of cache.keys()) {
    if (key.includes(endpoint)) {
      keysToDelete.push(key);
    }
  }
  
  keysToDelete.forEach(key => cache.delete(key));
}

/**
 * Gets cache statistics.
 * @returns {Object} Cache stats
 */
export function getCacheStats() {
  return {
    size: cache.size,
    maxSize: CACHE_CONFIG.MAX_CACHE_SIZE,
    entries: Array.from(cache.keys()).map(key => ({
      key,
      age: Date.now() - cache.get(key).timestamp
    }))
  };
}
