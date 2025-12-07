const CACHE_NAME = 'shabaka-player-v1';
const MEDIA_CACHE_NAME = 'shabaka-media-v1';
const API_CACHE_NAME = 'shabaka-api-v1';

const STATIC_ASSETS = [
    '/player/display',
    '/static/js/hls.min.js',
    '/static/js/mpegts.min.js',
    '/static/favicon-player.svg'
];

self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && 
                        cacheName !== MEDIA_CACHE_NAME && 
                        cacheName !== API_CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    if (event.request.url.includes('/static/uploads/')) {
        event.respondWith(handleMediaRequest(event.request));
        return;
    }
    
    if (event.request.url.includes('/player/api/playlist')) {
        event.respondWith(handlePlaylistRequest(event.request));
        return;
    }
    
    if (event.request.url.includes('/player/api/heartbeat') || 
        event.request.url.includes('/player/api/log-play')) {
        event.respondWith(handleApiRequest(event.request));
        return;
    }
    
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request).catch(() => {
                console.log('[SW] Network failed for:', event.request.url);
                return new Response('Offline', { status: 503 });
            });
        })
    );
});

async function handleMediaRequest(request) {
    const cache = await caches.open(MEDIA_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        console.log('[SW] Serving cached media:', request.url);
        
        fetch(request).then((networkResponse) => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
            }
        }).catch(() => {});
        
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            console.log('[SW] Caching new media:', request.url);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Media fetch failed:', request.url);
        return new Response('Media not available offline', { status: 503 });
    }
}

async function handlePlaylistRequest(request) {
    const cache = await caches.open(API_CACHE_NAME);
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            console.log('[SW] Caching playlist response');
            cache.put(request, networkResponse.clone());
            
            const playlistData = await networkResponse.clone().json();
            precachePlaylistMedia(playlistData);
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, serving cached playlist');
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return new Response(JSON.stringify({ 
            error: 'Offline - no cached playlist',
            offline: true 
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function handleApiRequest(request) {
    try {
        return await fetch(request);
    } catch (error) {
        console.log('[SW] API request failed (offline):', request.url);
        
        if (request.url.includes('/player/api/heartbeat')) {
            return new Response(JSON.stringify({ offline: true }), {
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        if (request.url.includes('/player/api/log-play')) {
            const body = await request.clone().json();
            await queueOfflineLog(body);
            return new Response(JSON.stringify({ queued: true, offline: true }), {
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        return new Response(JSON.stringify({ offline: true }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function precachePlaylistMedia(playlistData) {
    if (!playlistData.playlist || !Array.isArray(playlistData.playlist)) {
        return;
    }
    
    const mediaCache = await caches.open(MEDIA_CACHE_NAME);
    
    for (const item of playlistData.playlist) {
        if (item.url && !item.url.startsWith('http://') && !item.url.startsWith('https://')) {
            try {
                const cached = await mediaCache.match(item.url);
                if (!cached) {
                    console.log('[SW] Pre-caching media:', item.url);
                    const response = await fetch(item.url);
                    if (response.ok) {
                        await mediaCache.put(item.url, response);
                    }
                }
            } catch (error) {
                console.log('[SW] Failed to pre-cache:', item.url, error);
            }
        }
    }
}

async function queueOfflineLog(logData) {
    const db = await openOfflineDB();
    const tx = db.transaction('pendingLogs', 'readwrite');
    const store = tx.objectStore('pendingLogs');
    logData.timestamp = Date.now();
    await store.add(logData);
    console.log('[SW] Queued offline log:', logData);
}

function openOfflineDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('ShabakaPlayerOffline', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('pendingLogs')) {
                db.createObjectStore('pendingLogs', { keyPath: 'timestamp' });
            }
            
            if (!db.objectStoreNames.contains('cachedPlaylist')) {
                db.createObjectStore('cachedPlaylist', { keyPath: 'id' });
            }
        };
    });
}

self.addEventListener('message', async (event) => {
    if (event.data.type === 'PRECACHE_MEDIA') {
        const urls = event.data.urls;
        const mediaCache = await caches.open(MEDIA_CACHE_NAME);
        
        for (const url of urls) {
            try {
                const cached = await mediaCache.match(url);
                if (!cached) {
                    console.log('[SW] Pre-caching requested media:', url);
                    const response = await fetch(url);
                    if (response.ok) {
                        await mediaCache.put(url, response);
                    }
                }
            } catch (error) {
                console.log('[SW] Failed to pre-cache:', url);
            }
        }
        
        event.source.postMessage({ type: 'PRECACHE_COMPLETE', urls: urls });
    }
    
    if (event.data.type === 'SYNC_LOGS') {
        await syncPendingLogs();
        event.source.postMessage({ type: 'SYNC_COMPLETE' });
    }
    
    if (event.data.type === 'GET_CACHE_STATUS') {
        const status = await getCacheStatus();
        event.source.postMessage({ type: 'CACHE_STATUS', status: status });
    }
    
    if (event.data.type === 'CLEAR_OLD_MEDIA') {
        await clearOldMediaCache(event.data.keepUrls || []);
        event.source.postMessage({ type: 'CLEAR_COMPLETE' });
    }
});

async function syncPendingLogs() {
    try {
        const db = await openOfflineDB();
        const tx = db.transaction('pendingLogs', 'readonly');
        const store = tx.objectStore('pendingLogs');
        const logs = await store.getAll();
        
        if (!logs || logs.length === 0) {
            return;
        }
        
        console.log('[SW] Syncing', logs.length, 'pending logs');
        
        for (const log of logs) {
            try {
                const response = await fetch('/player/api/log-play', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(log)
                });
                
                if (response.ok) {
                    const deleteTx = db.transaction('pendingLogs', 'readwrite');
                    const deleteStore = deleteTx.objectStore('pendingLogs');
                    await deleteStore.delete(log.timestamp);
                    console.log('[SW] Synced log:', log.timestamp);
                }
            } catch (error) {
                console.log('[SW] Failed to sync log:', log.timestamp);
            }
        }
    } catch (error) {
        console.log('[SW] Error syncing logs:', error);
    }
}

async function getCacheStatus() {
    const mediaCache = await caches.open(MEDIA_CACHE_NAME);
    const keys = await mediaCache.keys();
    
    let totalSize = 0;
    const cachedUrls = [];
    
    for (const request of keys) {
        cachedUrls.push(request.url);
        try {
            const response = await mediaCache.match(request);
            if (response) {
                const blob = await response.clone().blob();
                totalSize += blob.size;
            }
        } catch (e) {}
    }
    
    return {
        mediaCount: keys.length,
        totalSize: totalSize,
        totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
        cachedUrls: cachedUrls
    };
}

async function clearOldMediaCache(keepUrls) {
    const mediaCache = await caches.open(MEDIA_CACHE_NAME);
    const keys = await mediaCache.keys();
    
    for (const request of keys) {
        if (!keepUrls.includes(request.url)) {
            console.log('[SW] Removing old cached media:', request.url);
            await mediaCache.delete(request);
        }
    }
}

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-logs') {
        event.waitUntil(syncPendingLogs());
    }
});
