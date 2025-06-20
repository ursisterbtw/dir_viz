/**
 * API Integration Layer
 * Handles all communication with the backend services
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.endpoints = {
            health: '/api/health',
            validatePath: '/api/validate-path',
            scanDirectory: '/api/scan-directory',
            directoryStats: '/api/directory-stats',
            fileContent: '/api/file-content',
            fileInfo: '/api/file-info',
            export: '/api/export',
            exportFormats: '/api/export-formats',
            config: '/api/config',
            cacheStats: '/api/cache-stats',
            clearCache: '/api/clear-cache'
        };
        
        this.requestTimeout = 30000; // 30 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        
        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        this.setupDefaultInterceptors();
    }
    
    setupDefaultInterceptors() {
        // Request interceptor for adding common headers
        this.addRequestInterceptor((config) => {
            config.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...config.headers
            };
            return config;
        });
        
        // Response interceptor for error handling
        this.addResponseInterceptor(
            (response) => response,
            (error) => {
                console.error('API Error:', error);
                this.handleAPIError(error);
                return Promise.reject(error);
            }
        );
    }
    
    addRequestInterceptor(onFulfilled, onRejected) {
        this.requestInterceptors.push({ onFulfilled, onRejected });
    }
    
    addResponseInterceptor(onFulfilled, onRejected) {
        this.responseInterceptors.push({ onFulfilled, onRejected });
    }
    
    async request(url, options = {}) {
        // Apply request interceptors
        let config = {
            method: 'GET',
            headers: {},
            timeout: this.requestTimeout,
            ...options
        };
        
        for (const interceptor of this.requestInterceptors) {
            try {
                config = interceptor.onFulfilled ? interceptor.onFulfilled(config) : config;
            } catch (error) {
                if (interceptor.onRejected) {
                    interceptor.onRejected(error);
                }
                throw error;
            }
        }
        
        // Make request with retry logic
        let lastError;
        for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
            try {
                const response = await this.makeRequest(url, config);
                
                // Apply response interceptors
                let processedResponse = response;
                for (const interceptor of this.responseInterceptors) {
                    try {
                        processedResponse = interceptor.onFulfilled ? 
                            interceptor.onFulfilled(processedResponse) : processedResponse;
                    } catch (error) {
                        if (interceptor.onRejected) {
                            interceptor.onRejected(error);
                        }
                        throw error;
                    }
                }
                
                return processedResponse;
                
            } catch (error) {
                lastError = error;
                
                // Don't retry on certain error codes
                if (error.status && [400, 401, 403, 404].includes(error.status)) {
                    break;
                }
                
                // Wait before retry
                if (attempt < this.retryAttempts - 1) {
                    await this.delay(this.retryDelay * Math.pow(2, attempt));
                }
            }
        }
        
        throw lastError;
    }
    
    async makeRequest(url, config) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);
        
        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new APIError(response.status, errorData.detail || response.statusText, errorData);
            }
            
            const data = await response.json();
            return { data, status: response.status, headers: response.headers };
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new APIError(408, 'Request timeout');
            }
            
            throw error;
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    handleAPIError(error) {
        // Dispatch global error event
        const event = new CustomEvent('apiError', {
            detail: {
                error: error,
                timestamp: new Date().toISOString()
            }
        });
        document.dispatchEvent(event);
        
        // Update UI status
        this.updateStatus('error', error.message || 'API Error occurred');
    }
    
    updateStatus(type, message) {
        const statusText = document.getElementById('status-text');
        const statusIndicator = document.getElementById('status-indicator');
        
        if (statusText) {
            statusText.textContent = message;
        }
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${type}`;
        }
        
        // Auto-clear success messages
        if (type === 'success') {
            setTimeout(() => {
                if (statusText) statusText.textContent = 'Ready';
                if (statusIndicator) statusIndicator.className = 'status-indicator';
            }, 3000);
        }
    }
    
    // API Methods
    async healthCheck() {
        try {
            const response = await this.request(this.endpoints.health);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Health check failed', error);
        }
    }
    
    async validatePath(path) {
        try {
            this.updateStatus('loading', 'Validating path...');
            const response = await this.request(this.endpoints.validatePath, {
                method: 'POST',
                body: JSON.stringify({ path })
            });
            
            this.updateStatus('success', 'Path validated');
            return response.data;
        } catch (error) {
            this.updateStatus('error', 'Path validation failed');
            throw error;
        }
    }
    
    async scanDirectory(path, options = {}) {
        const {
            maxDepth = 5,
            useCache = true,
            onProgress = null
        } = options;
        
        try {
            this.updateStatus('loading', 'Scanning directory...');
            
            const requestData = {
                path,
                max_depth: maxDepth,
                use_cache: useCache
            };
            
            const response = await this.request(this.endpoints.scanDirectory, {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
            
            if (response.data.success) {
                this.updateStatus('success', `Scanned ${response.data.metadata.file_count} files`);
                return {
                    tree: response.data.tree,
                    metadata: response.data.metadata
                };
            } else {
                throw new APIError(500, 'Scan failed', response.data);
            }
            
        } catch (error) {
            this.updateStatus('error', 'Directory scan failed');
            throw error;
        }
    }
    
    async getDirectoryStats(path) {
        try {
            const response = await this.request(`${this.endpoints.directoryStats}?path=${encodeURIComponent(path)}`);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get directory stats', error);
        }
    }
    
    async getFileContent(filePath, options = {}) {
        const {
            maxLines = null,
            encoding = 'utf-8'
        } = options;
        
        try {
            let url = `${this.endpoints.fileContent}?file_path=${encodeURIComponent(filePath)}&encoding=${encoding}`;
            if (maxLines) {
                url += `&max_lines=${maxLines}`;
            }
            
            const response = await this.request(url);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get file content', error);
        }
    }
    
    async getFileInfo(filePath) {
        try {
            const response = await this.request(`${this.endpoints.fileInfo}?file_path=${encodeURIComponent(filePath)}`);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get file info', error);
        }
    }
    
    async exportVisualization(exportRequest) {
        try {
            this.updateStatus('loading', 'Exporting visualization...');
            
            const response = await this.request(this.endpoints.export, {
                method: 'POST',
                body: JSON.stringify(exportRequest)
            });
            
            if (response.data.success) {
                this.updateStatus('success', 'Export completed');
                return response.data;
            } else {
                throw new APIError(500, 'Export failed', response.data);
            }
            
        } catch (error) {
            this.updateStatus('error', 'Export failed');
            throw error;
        }
    }
    
    async getExportFormats() {
        try {
            const response = await this.request(this.endpoints.exportFormats);
            return response.data.formats;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get export formats', error);
        }
    }
    
    async getConfig() {
        try {
            const response = await this.request(this.endpoints.config);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get config', error);
        }
    }
    
    async getCacheStats() {
        try {
            const response = await this.request(this.endpoints.cacheStats);
            return response.data;
        } catch (error) {
            throw new APIError(error.status || 500, 'Failed to get cache stats', error);
        }
    }
    
    async clearCache() {
        try {
            this.updateStatus('loading', 'Clearing cache...');
            
            const response = await this.request(this.endpoints.clearCache, {
                method: 'POST'
            });
            
            if (response.data.success) {
                this.updateStatus('success', 'Cache cleared');
                return response.data;
            } else {
                throw new APIError(500, 'Cache clear failed', response.data);
            }
            
        } catch (error) {
            this.updateStatus('error', 'Cache clear failed');
            throw error;
        }
    }
    
    // WebSocket connection for real-time updates
    connectWebSocket(options = {}) {
        const {
            userId = null,
            roomId = null,
            onMessage = null,
            onError = null,
            onClose = null,
            onOpen = null
        } = options;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let wsUrl = `${protocol}//${window.location.host}/ws`;
        
        const params = new URLSearchParams();
        if (userId) params.append('user_id', userId);
        if (roomId) params.append('room_id', roomId);
        
        if (params.toString()) {
            wsUrl += `?${params.toString()}`;
        }
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = (event) => {
            console.log('WebSocket connected');
            if (onOpen) onOpen(event);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (onError) onError(event);
        };
        
        ws.onclose = (event) => {
            console.log('WebSocket closed:', event);
            if (onClose) onClose(event);
        };
        
        return ws;
    }
    
    // Utility methods
    buildURL(endpoint, params = {}) {
        const url = new URL(endpoint, this.baseURL);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        return url.toString();
    }
    
    downloadFile(data, filename, contentType = 'application/octet-stream') {
        const blob = new Blob([data], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
}

// Custom Error class for API errors
class APIError extends Error {
    constructor(status, message, data = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
    
    toString() {
        return `APIError(${this.status}): ${this.message}`;
    }
}

// Request/Response logging (for development)
class APILogger {
    constructor(enabled = false) {
        this.enabled = enabled;
        this.logs = [];
        this.maxLogs = 100;
    }
    
    log(type, data) {
        if (!this.enabled) return;
        
        const entry = {
            type,
            data,
            timestamp: new Date().toISOString()
        };
        
        this.logs.unshift(entry);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        console.log(`[API ${type.toUpperCase()}]`, data);
    }
    
    getLogs() {
        return this.logs;
    }
    
    clearLogs() {
        this.logs = [];
    }
    
    enable() {
        this.enabled = true;
    }
    
    disable() {
        this.enabled = false;
    }
}

// Performance monitoring
class APIPerformanceMonitor {
    constructor() {
        this.metrics = new Map();
    }
    
    startTimer(key) {
        this.metrics.set(key, { startTime: performance.now() });
    }
    
    endTimer(key) {
        const metric = this.metrics.get(key);
        if (metric) {
            metric.endTime = performance.now();
            metric.duration = metric.endTime - metric.startTime;
            return metric.duration;
        }
        return null;
    }
    
    getMetrics() {
        const result = {};
        this.metrics.forEach((value, key) => {
            if (value.duration !== undefined) {
                result[key] = value.duration;
            }
        });
        return result;
    }
    
    clearMetrics() {
        this.metrics.clear();
    }
}

// Export classes
window.APIClient = APIClient;
window.APIError = APIError;
window.APILogger = APILogger;
window.APIPerformanceMonitor = APIPerformanceMonitor;

// Create global API client instance
window.apiClient = new APIClient();

// Optional: Enable logging in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.apiLogger = new APILogger(true);
    window.apiClient.addRequestInterceptor((config) => {
        window.apiLogger.log('request', config);
        return config;
    });
    window.apiClient.addResponseInterceptor((response) => {
        window.apiLogger.log('response', response);
        return response;
    });
}