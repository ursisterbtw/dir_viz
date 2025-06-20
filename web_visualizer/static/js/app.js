/**
 * Main Application Controller
 * Orchestrates all components and handles user interactions
 */

class DirectoryVisualizerApp {
    constructor() {
        this.visualization = null;
        this.currentData = null;
        this.currentPath = '';
        this.settings = {
            maxDepth: 5,
            showFiles: true,
            showSizes: true,
            animateNodes: true,
            particleEffects: true,
            layout: 'tree',
            theme: 'neon',
            animationDuration: 900,
            maxNodes: 1000
        };
        
        this.isScanning = false;
        this.websocket = null;
        this.fpsCounter = new FPSCounter();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.loadSettings();
        this.initializeVisualization();
        this.setupPerformanceMonitoring();
        this.connectWebSocket();
        
        // Health check on startup
        this.performHealthCheck();
        
        // Load configuration
        this.loadConfiguration();
        
        console.log('🚀 Directory Visualizer App initialized');
    }
    
    setupEventListeners() {
        // Scan controls
        document.getElementById('scan-btn').addEventListener('click', () => this.scanDirectory());
        document.getElementById('path-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.scanDirectory();
        });
        
        // Depth slider
        const depthSlider = document.getElementById('depth-slider');
        const depthValue = document.getElementById('depth-value');
        depthSlider.addEventListener('input', (e) => {
            this.settings.maxDepth = parseInt(e.target.value);
            depthValue.textContent = e.target.value;
        });
        
        // Layout selector
        document.getElementById('layout-select').addEventListener('change', (e) => {
            this.settings.layout = e.target.value;
            this.changeLayout(e.target.value);
        });
        
        // Visualization options
        document.getElementById('show-files').addEventListener('change', (e) => {
            this.settings.showFiles = e.target.checked;
            this.updateVisualization();
        });
        
        document.getElementById('show-sizes').addEventListener('change', (e) => {
            this.settings.showSizes = e.target.checked;
            this.updateVisualization();
        });
        
        document.getElementById('animate-nodes').addEventListener('change', (e) => {
            this.settings.animateNodes = e.target.checked;
        });
        
        document.getElementById('particle-effects').addEventListener('change', (e) => {
            this.settings.particleEffects = e.target.checked;
            this.toggleParticleEffects(e.target.checked);
        });
        
        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoom-out').addEventListener('click', () => this.zoomOut());
        document.getElementById('reset-zoom').addEventListener('click', () => this.resetZoom());
        document.getElementById('auto-fit').addEventListener('click', () => this.autoFit());
        
        // Export controls
        document.getElementById('export-btn').addEventListener('click', () => this.exportVisualization());
        
        // Settings modal
        document.getElementById('settings-btn').addEventListener('click', () => this.showSettingsModal());
        document.getElementById('settings-close').addEventListener('click', () => this.hideSettingsModal());
        
        // Fullscreen toggle
        document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());
        
        // Theme buttons
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const theme = e.currentTarget.getAttribute('data-theme');
                this.changeTheme(theme);
            });
        });
        
        // Error retry
        document.getElementById('retry-btn').addEventListener('click', () => this.retryLastOperation());
        
        // Custom events
        document.addEventListener('nodeClicked', (e) => this.handleNodeClick(e.detail));
        document.addEventListener('nodeDoubleClicked', (e) => this.handleNodeDoubleClick(e.detail));
        document.addEventListener('apiError', (e) => this.handleAPIError(e.detail));
        document.addEventListener('themeChanged', (e) => this.handleThemeChange(e.detail));
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('resize', () => this.handleResize());
        
        // Modal background clicks
        document.getElementById('settings-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.hideSettingsModal();
            }
        });
        
        // Performance monitoring
        setInterval(() => this.updatePerformanceStats(), 1000);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            const key = e.key.toLowerCase();
            const ctrl = e.ctrlKey || e.metaKey;
            const shift = e.shiftKey;
            
            switch (key) {
                case 'r':
                    if (ctrl) {
                        e.preventDefault();
                        this.scanDirectory();
                    }
                    break;
                    
                case 'f':
                    if (ctrl) {
                        e.preventDefault();
                        this.autoFit();
                    }
                    break;
                    
                case '=':
                case '+':
                    if (ctrl) {
                        e.preventDefault();
                        this.zoomIn();
                    }
                    break;
                    
                case '-':
                    if (ctrl) {
                        e.preventDefault();
                        this.zoomOut();
                    }
                    break;
                    
                case '0':
                    if (ctrl) {
                        e.preventDefault();
                        this.resetZoom();
                    }
                    break;
                    
                case 'escape':
                    this.hideSettingsModal();
                    this.hideTooltip();
                    break;
                    
                case 's':
                    if (ctrl) {
                        e.preventDefault();
                        this.exportVisualization();
                    }
                    break;
                    
                case 't':
                    if (ctrl && shift) {
                        e.preventDefault();
                        window.themeManager.cycleTheme();
                    }
                    break;
                    
                case 'f11':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                    
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                case '6':
                    if (ctrl) {
                        e.preventDefault();
                        const layouts = ['tree', 'force', 'radial', 'treemap', 'sunburst', 'galaxy'];
                        const layoutIndex = parseInt(key) - 1;
                        if (layouts[layoutIndex]) {
                            this.changeLayout(layouts[layoutIndex]);
                        }
                    }
                    break;
            }
        });
    }
    
    loadSettings() {
        const saved = localStorage.getItem('directory-viz-settings');
        if (saved) {
            try {
                const savedSettings = JSON.parse(saved);
                this.settings = { ...this.settings, ...savedSettings };
                this.applySettings();
            } catch (error) {
                console.warn('Failed to load saved settings:', error);
            }
        }
    }
    
    saveSettings() {
        localStorage.setItem('directory-viz-settings', JSON.stringify(this.settings));
    }
    
    applySettings() {
        // Update UI controls
        document.getElementById('depth-slider').value = this.settings.maxDepth;
        document.getElementById('depth-value').textContent = this.settings.maxDepth;
        document.getElementById('layout-select').value = this.settings.layout;
        document.getElementById('show-files').checked = this.settings.showFiles;
        document.getElementById('show-sizes').checked = this.settings.showSizes;
        document.getElementById('animate-nodes').checked = this.settings.animateNodes;
        document.getElementById('particle-effects').checked = this.settings.particleEffects;
        
        // Update visualization
        if (this.visualization) {
            this.visualization.updateSettings(this.settings);
        }
        
        // Update particle effects
        this.toggleParticleEffects(this.settings.particleEffects);
    }
    
    initializeVisualization() {
        this.visualization = new VisualizationEngine('visualization');
    }
    
    setupPerformanceMonitoring() {
        this.fpsCounter.start();
        
        // Monitor memory usage if available
        if (performance.memory) {
            setInterval(() => {
                const memory = performance.memory;
                const usedMB = Math.round(memory.usedJSHeapSize / 1048576);
                const limitMB = Math.round(memory.jsHeapSizeLimit / 1048576);
                console.debug(`Memory: ${usedMB}MB / ${limitMB}MB`);
            }, 10000);
        }
    }
    
    connectWebSocket() {
        try {
            this.websocket = window.apiClient.connectWebSocket({
                onMessage: (data) => this.handleWebSocketMessage(data),
                onError: (error) => console.warn('WebSocket error:', error),
                onClose: () => console.log('WebSocket disconnected'),
                onOpen: () => console.log('WebSocket connected')
            });
        } catch (error) {
            console.warn('WebSocket connection failed:', error);
        }
    }
    
    async performHealthCheck() {
        try {
            const health = await window.apiClient.healthCheck();
            console.log('✅ Backend health check passed:', health);
        } catch (error) {
            console.error('❌ Backend health check failed:', error);
            this.showError('Backend service is not available');
        }
    }
    
    async loadConfiguration() {
        try {
            const config = await window.apiClient.getConfig();
            console.log('📄 Configuration loaded:', config);
            
            // Update settings with server config
            if (config.max_depth) {
                this.settings.maxDepth = Math.min(this.settings.maxDepth, config.max_depth);
            }
            
            this.applySettings();
        } catch (error) {
            console.warn('Failed to load configuration:', error);
        }
    }
    
    // Core functionality
    async scanDirectory() {
        const pathInput = document.getElementById('path-input');
        const path = pathInput.value.trim();
        
        if (!path) {
            this.showError('Please enter a directory path');
            return;
        }
        
        if (this.isScanning) {
            console.warn('Scan already in progress');
            return;
        }
        
        this.isScanning = true;
        this.currentPath = path;
        this.showLoading('Scanning directory...');
        
        try {
            // Validate path first
            await window.apiClient.validatePath(path);
            
            // Perform scan
            const result = await window.apiClient.scanDirectory(path, {
                maxDepth: this.settings.maxDepth,
                useCache: true
            });
            
            this.hideLoading();
            this.currentData = result.tree;
            
            // Update UI
            document.getElementById('current-path').textContent = path;
            this.updateBreadcrumb(path);
            
            // Render visualization
            this.visualization.setData(result.tree);
            
            // Auto-fit after rendering
            setTimeout(() => this.autoFit(), 500);
            
            console.log('✅ Directory scan completed:', result.metadata);
            
        } catch (error) {
            this.hideLoading();
            this.showError(`Scan failed: ${error.message}`);
            console.error('Directory scan failed:', error);
        } finally {
            this.isScanning = false;
        }
    }
    
    changeLayout(layout) {
        this.settings.layout = layout;
        this.saveSettings();
        
        if (this.visualization && this.currentData) {
            this.visualization.setLayout(layout);
            
            // Auto-fit after layout change
            setTimeout(() => this.autoFit(), 800);
        }
        
        console.log(`Layout changed to: ${layout}`);
    }
    
    changeTheme(theme) {
        if (window.themeManager) {
            window.themeManager.setTheme(theme);
            this.settings.theme = theme;
            this.saveSettings();
        }
    }
    
    updateVisualization() {
        if (this.visualization && this.currentData) {
            this.visualization.render(this.currentData, this.settings.animateNodes);
        }
    }
    
    // Zoom and navigation
    zoomIn() {
        if (this.visualization) {
            // Implement zoom in via the visualization engine
            const currentZoom = this.visualization.currentTransform.k;
            const newZoom = Math.min(currentZoom * 1.5, 10);
            this.setZoom(newZoom);
        }
    }
    
    zoomOut() {
        if (this.visualization) {
            const currentZoom = this.visualization.currentTransform.k;
            const newZoom = Math.max(currentZoom / 1.5, 0.1);
            this.setZoom(newZoom);
        }
    }
    
    resetZoom() {
        if (this.visualization) {
            this.visualization.resetZoom();
        }
    }
    
    autoFit() {
        if (this.visualization) {
            this.visualization.autoFit();
        }
    }
    
    setZoom(scale) {
        if (this.visualization) {
            const transform = this.visualization.currentTransform;
            const newTransform = d3.zoomIdentity
                .translate(transform.x, transform.y)
                .scale(scale);
            
            this.visualization.svg.transition()
                .duration(600)
                .ease(d3.easeCubicOut)
                .call(this.visualization.zoom.transform, newTransform);
        }
    }
    
    // Export functionality
    async exportVisualization() {
        const format = document.getElementById('export-format').value;
        
        if (!this.currentData) {
            this.showError('No data to export');
            return;
        }
        
        try {
            this.showLoading('Exporting visualization...');
            
            const exportRequest = {
                format: format,
                path: this.currentPath,
                settings: {
                    color_scheme: this.settings.theme,
                    show_file_sizes: this.settings.showSizes,
                    show_file_counts: true,
                    max_depth: this.settings.maxDepth,
                    collapse_large_directories: true,
                    large_directory_threshold: 50,
                    show_hidden_files: false,
                    highlight_extensions: []
                },
                include_annotations: false,
                high_resolution: false
            };
            
            const result = await window.apiClient.exportVisualization(exportRequest);
            
            if (result.success) {
                // Handle different export types
                if (format === 'svg' && this.visualization) {
                    const svgContent = this.visualization.exportSVG();
                    window.apiClient.downloadFile(svgContent, `directory-viz.${format}`, 'image/svg+xml');
                } else if (result.file_path) {
                    // Download from server
                    window.open(result.file_path, '_blank');
                }
                
                this.hideLoading();
                console.log('✅ Export completed');
            } else {
                throw new Error(result.error || 'Export failed');
            }
            
        } catch (error) {
            this.hideLoading();
            this.showError(`Export failed: ${error.message}`);
            console.error('Export failed:', error);
        }
    }
    
    // UI Management
    showLoading(message) {
        const spinner = document.getElementById('loading-spinner');
        const errorMsg = document.getElementById('error-message');
        
        if (spinner) {
            spinner.querySelector('p').textContent = message;
            spinner.classList.remove('hidden');
        }
        
        if (errorMsg) {
            errorMsg.classList.add('hidden');
        }
    }
    
    hideLoading() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.classList.add('hidden');
        }
    }
    
    showError(message) {
        const errorMsg = document.getElementById('error-message');
        const spinner = document.getElementById('loading-spinner');
        
        if (errorMsg) {
            errorMsg.querySelector('#error-text').textContent = message;
            errorMsg.classList.remove('hidden');
        }
        
        if (spinner) {
            spinner.classList.add('hidden');
        }
    }
    
    hideError() {
        const errorMsg = document.getElementById('error-message');
        if (errorMsg) {
            errorMsg.classList.add('hidden');
        }
    }
    
    showSettingsModal() {
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // Load current settings
            document.getElementById('animation-duration').value = this.settings.animationDuration;
            document.getElementById('max-nodes').value = this.settings.maxNodes;
        }
    }
    
    hideSettingsModal() {
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.classList.add('hidden');
            
            // Save settings
            this.settings.animationDuration = parseInt(document.getElementById('animation-duration').value);
            this.settings.maxNodes = parseInt(document.getElementById('max-nodes').value);
            this.saveSettings();
            
            // Apply new settings
            if (this.visualization) {
                this.visualization.updateSettings(this.settings);
            }
        }
    }
    
    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.classList.add('hidden');
        }
    }
    
    updateBreadcrumb(path) {
        const breadcrumb = document.getElementById('breadcrumb');
        if (breadcrumb) {
            const parts = path.split('/').filter(part => part);
            breadcrumb.textContent = parts.length > 3 ? 
                `.../${parts.slice(-3).join('/')}` : 
                path;
        }
    }
    
    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    }
    
    toggleParticleEffects(enabled) {
        if (window.particleSystem) {
            if (enabled) {
                window.particleSystem.resume();
            } else {
                window.particleSystem.pause();
            }
        }
    }
    
    updatePerformanceStats() {
        const fpsElement = document.getElementById('fps-counter');
        if (fpsElement) {
            fpsElement.textContent = `${this.fpsCounter.getFPS()} FPS`;
        }
    }
    
    // Event handlers
    handleNodeClick(detail) {
        console.log('Node clicked:', detail.node);
        
        // Could show file content, properties, etc.
        if (detail.node.type === 'file') {
            // this.showFileInfo(detail.node);
        }
    }
    
    handleNodeDoubleClick(detail) {
        console.log('Node double-clicked:', detail.node);
        
        // Could navigate to directory, open file, etc.
        if (detail.node.type === 'directory') {
            // this.navigateToDirectory(detail.node.path);
        }
    }
    
    handleAPIError(detail) {
        console.error('API Error:', detail.error);
        this.showError(`API Error: ${detail.error.message}`);
    }
    
    handleThemeChange(detail) {
        console.log('Theme changed to:', detail.theme);
        this.settings.theme = detail.theme;
        this.saveSettings();
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);
        
        // Handle real-time updates, collaboration, etc.
        switch (data.type) {
            case 'file_changed':
                // Refresh visualization if current path is affected
                if (data.path && this.currentPath.startsWith(data.path)) {
                    this.scanDirectory();
                }
                break;
                
            case 'user_joined':
                console.log('User joined:', data.user);
                break;
                
            case 'annotation_added':
                // Handle collaborative annotations
                break;
        }
    }
    
    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            if (this.visualization) {
                this.visualization.resize();
            }
        }, 250);
    }
    
    retryLastOperation() {
        this.hideError();
        if (this.currentPath) {
            this.scanDirectory();
        }
    }
    
    cleanup() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        if (this.visualization) {
            this.visualization.destroy();
        }
        
        this.saveSettings();
    }
}

// FPS Counter utility
class FPSCounter {
    constructor() {
        this.fps = 60;
        this.frames = 0;
        this.lastTime = performance.now();
        this.isRunning = false;
    }
    
    start() {
        this.isRunning = true;
        this.update();
    }
    
    stop() {
        this.isRunning = false;
    }
    
    update() {
        if (!this.isRunning) return;
        
        this.frames++;
        const currentTime = performance.now();
        
        if (currentTime >= this.lastTime + 1000) {
            this.fps = Math.round((this.frames * 1000) / (currentTime - this.lastTime));
            this.frames = 0;
            this.lastTime = currentTime;
        }
        
        requestAnimationFrame(() => this.update());
    }
    
    getFPS() {
        return this.fps;
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎮 Initializing Directory Visualizer App...');
    window.app = new DirectoryVisualizerApp();
});

// Handle page visibility changes for performance
document.addEventListener('visibilitychange', () => {
    if (window.app) {
        if (document.hidden) {
            // Pause animations when tab is not visible
            if (window.app.fpsCounter) {
                window.app.fpsCounter.stop();
            }
        } else {
            // Resume animations when tab becomes visible
            if (window.app.fpsCounter) {
                window.app.fpsCounter.start();
            }
        }
    }
});

// Export for global access
window.DirectoryVisualizerApp = DirectoryVisualizerApp;