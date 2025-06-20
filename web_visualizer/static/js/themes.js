/**
 * Theme Management System
 * Handles dynamic theme switching with visual effects
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'neon';
        this.themes = {
            neon: {
                name: 'Neon',
                colors: {
                    primary: '#00ff99',
                    secondary: '#00ffcc',
                    accent: '#ff00cc',
                    warning: '#ffff00',
                    danger: '#ff3366',
                    blue: '#33ccff',
                    bgPrimary: '#0a0a0a',
                    bgSecondary: '#121212',
                    bgTertiary: '#1a1a1a',
                    textPrimary: '#ffffff',
                    textSecondary: '#cccccc',
                    textMuted: '#888888'
                },
                particleColors: [
                    'rgba(0, 255, 153, 0.6)',
                    'rgba(0, 255, 204, 0.4)',
                    'rgba(51, 204, 255, 0.5)',
                    'rgba(255, 0, 204, 0.3)',
                    'rgba(255, 255, 0, 0.4)'
                ]
            },
            cyber: {
                name: 'Cyber',
                colors: {
                    primary: '#00ffff',
                    secondary: '#0080ff',
                    accent: '#8000ff',
                    warning: '#ff8000',
                    danger: '#ff0040',
                    blue: '#0040ff',
                    bgPrimary: '#000510',
                    bgSecondary: '#0a0f1a',
                    bgTertiary: '#101520',
                    textPrimary: '#e0f0ff',
                    textSecondary: '#b0d0e0',
                    textMuted: '#7090a0'
                },
                particleColors: [
                    'rgba(0, 255, 255, 0.6)',
                    'rgba(0, 128, 255, 0.4)',
                    'rgba(128, 0, 255, 0.5)',
                    'rgba(255, 0, 128, 0.3)',
                    'rgba(0, 255, 128, 0.4)'
                ]
            },
            matrix: {
                name: 'Matrix',
                colors: {
                    primary: '#00ff00',
                    secondary: '#80ff00',
                    accent: '#ffff00',
                    warning: '#ff8000',
                    danger: '#ff4000',
                    blue: '#00ff80',
                    bgPrimary: '#000500',
                    bgSecondary: '#001000',
                    bgTertiary: '#002000',
                    textPrimary: '#e0ffe0',
                    textSecondary: '#c0ffc0',
                    textMuted: '#80c080'
                },
                particleColors: [
                    'rgba(0, 255, 0, 0.6)',
                    'rgba(128, 255, 0, 0.4)',
                    'rgba(255, 255, 0, 0.5)',
                    'rgba(0, 255, 128, 0.3)',
                    'rgba(128, 255, 128, 0.4)'
                ]
            },
            synthwave: {
                name: 'Synthwave',
                colors: {
                    primary: '#ff0080',
                    secondary: '#ff8000',
                    accent: '#ffff00',
                    warning: '#ff0040',
                    danger: '#ff0000',
                    blue: '#8000ff',
                    bgPrimary: '#100010',
                    bgSecondary: '#200020',
                    bgTertiary: '#300030',
                    textPrimary: '#ffe0ff',
                    textSecondary: '#ffb0ff',
                    textMuted: '#c080c0'
                },
                particleColors: [
                    'rgba(255, 0, 128, 0.6)',
                    'rgba(255, 128, 0, 0.4)',
                    'rgba(255, 255, 0, 0.5)',
                    'rgba(255, 0, 255, 0.3)',
                    'rgba(128, 0, 255, 0.4)'
                ]
            }
        };
        
        this.transitionDuration = 800;
        this.init();
    }
    
    init() {
        this.loadSavedTheme();
        this.setupEventListeners();
        this.setupThemeButtons();
        this.applyTheme(this.currentTheme, false);
    }
    
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('directory-viz-theme');
        if (savedTheme && this.themes[savedTheme]) {
            this.currentTheme = savedTheme;
        }
    }
    
    setupEventListeners() {
        // Theme toggle button
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.cycleTheme());
        }
        
        // System theme change detection
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            this.handleSystemThemeChange(e.matches);
        });
        
        // Theme change from other sources
        document.addEventListener('themeChangeRequest', (e) => {
            this.applyTheme(e.detail.theme);
        });
    }
    
    setupThemeButtons() {
        const themeButtons = document.querySelectorAll('.theme-btn');
        themeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const theme = button.getAttribute('data-theme');
                if (theme && this.themes[theme]) {
                    this.applyTheme(theme);
                }
            });
        });
    }
    
    cycleTheme() {
        const themeNames = Object.keys(this.themes);
        const currentIndex = themeNames.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themeNames.length;
        const nextTheme = themeNames[nextIndex];
        
        this.applyTheme(nextTheme);
    }
    
    applyTheme(themeName, animate = true) {
        if (!this.themes[themeName]) {
            console.warn(`Theme '${themeName}' not found`);
            return;
        }
        
        const theme = this.themes[themeName];
        const oldTheme = this.currentTheme;
        this.currentTheme = themeName;
        
        // Save to localStorage
        localStorage.setItem('directory-viz-theme', themeName);
        
        if (animate) {
            this.animateThemeTransition(theme, oldTheme);
        } else {
            this.setThemeColors(theme);
        }
        
        this.updateThemeButtons();
        this.dispatchThemeChange(themeName, theme);
    }
    
    animateThemeTransition(newTheme, oldThemeName) {
        const body = document.body;
        
        // Add transition class
        body.classList.add('theme-transitioning');
        
        // Create overlay for smooth transition
        const overlay = document.createElement('div');
        overlay.className = 'theme-transition-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at center, 
                ${newTheme.colors.primary}20 0%, 
                ${newTheme.colors.bgPrimary} 100%);
            z-index: 10000;
            opacity: 0;
            pointer-events: none;
            transition: opacity ${this.transitionDuration}ms ease;
        `;
        
        document.body.appendChild(overlay);
        
        // Trigger overlay animation
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
        });
        
        // Apply new theme colors after half transition
        setTimeout(() => {
            this.setThemeColors(newTheme);
            overlay.style.opacity = '0';
        }, this.transitionDuration / 2);
        
        // Clean up
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
            body.classList.remove('theme-transitioning');
        }, this.transitionDuration);
        
        // Add theme change effects
        this.addThemeChangeEffects(newTheme);
    }
    
    setThemeColors(theme) {
        const root = document.documentElement;
        
        Object.entries(theme.colors).forEach(([key, value]) => {
            const cssVarName = key.replace(/([A-Z])/g, '-$1').toLowerCase();
            root.style.setProperty(`--${cssVarName}`, value);
        });
        
        // Update specific CSS variables
        root.style.setProperty('--neon-primary', theme.colors.primary);
        root.style.setProperty('--neon-secondary', theme.colors.secondary);
        root.style.setProperty('--neon-accent', theme.colors.accent);
        root.style.setProperty('--neon-warning', theme.colors.warning);
        root.style.setProperty('--neon-danger', theme.colors.danger);
        root.style.setProperty('--neon-blue', theme.colors.blue);
        
        root.style.setProperty('--bg-primary', theme.colors.bgPrimary);
        root.style.setProperty('--bg-secondary', theme.colors.bgSecondary);
        root.style.setProperty('--bg-tertiary', theme.colors.bgTertiary);
        
        root.style.setProperty('--text-primary', theme.colors.textPrimary);
        root.style.setProperty('--text-secondary', theme.colors.textSecondary);
        root.style.setProperty('--text-muted', theme.colors.textMuted);
        
        // Update shadows and borders
        root.style.setProperty('--border-neon', `rgba(${this.hexToRgb(theme.colors.primary)}, 0.5)`);
        root.style.setProperty('--shadow-neon', `0 0 20px rgba(${this.hexToRgb(theme.colors.primary)}, 0.3)`);
        root.style.setProperty('--shadow-accent', `0 0 20px rgba(${this.hexToRgb(theme.colors.accent)}, 0.3)`);
    }
    
    addThemeChangeEffects(theme) {
        // Create particle burst effect
        this.createParticleBurst(theme);
        
        // Flash effect on important elements
        const importantElements = document.querySelectorAll('.logo, .btn-primary, .stat-value');
        importantElements.forEach(element => {
            element.style.animation = 'none';
            element.offsetHeight; // Trigger reflow
            element.style.animation = 'theme-flash 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
        });
        
        // Pulse effect on the visualization
        const visualization = document.getElementById('visualization');
        if (visualization) {
            visualization.style.filter = `drop-shadow(0 0 20px ${theme.colors.primary}40)`;
            setTimeout(() => {
                visualization.style.filter = '';
            }, 1000);
        }
    }
    
    createParticleBurst(theme) {
        const burstContainer = document.createElement('div');
        burstContainer.className = 'theme-burst-container';
        burstContainer.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            pointer-events: none;
            z-index: 9999;
        `;
        
        document.body.appendChild(burstContainer);
        
        // Create burst particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'theme-burst-particle';
            
            const angle = (i / 20) * Math.PI * 2;
            const distance = 100 + Math.random() * 100;
            const size = 4 + Math.random() * 8;
            
            particle.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: ${theme.colors.primary};
                border-radius: 50%;
                box-shadow: 0 0 10px ${theme.colors.primary};
                transform: translate(-50%, -50%);
                animation: theme-burst-particle 1s ease-out forwards;
                --end-x: ${Math.cos(angle) * distance}px;
                --end-y: ${Math.sin(angle) * distance}px;
            `;
            
            burstContainer.appendChild(particle);
        }
        
        // Clean up
        setTimeout(() => {
            if (burstContainer.parentNode) {
                burstContainer.parentNode.removeChild(burstContainer);
            }
        }, 1000);
    }
    
    updateThemeButtons() {
        const themeButtons = document.querySelectorAll('.theme-btn');
        themeButtons.forEach(button => {
            const theme = button.getAttribute('data-theme');
            if (theme === this.currentTheme) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }
    
    dispatchThemeChange(themeName, theme) {
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: themeName,
                colors: theme.colors,
                particleColors: theme.particleColors
            }
        });
        
        document.dispatchEvent(event);
    }
    
    handleSystemThemeChange(isDark) {
        // Optional: Auto-switch based on system preference
        // This can be enabled via settings
        const autoThemeSwitch = localStorage.getItem('directory-viz-auto-theme') === 'true';
        
        if (autoThemeSwitch) {
            const preferredTheme = isDark ? 'neon' : 'cyber';
            this.applyTheme(preferredTheme);
        }
    }
    
    // Utility methods
    hexToRgb(hex) {
        const result = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex);
        return result ? 
            `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : 
            '0, 0, 0';
    }
    
    getCurrentTheme() {
        return {
            name: this.currentTheme,
            ...this.themes[this.currentTheme]
        };
    }
    
    getAvailableThemes() {
        return Object.keys(this.themes).map(key => ({
            id: key,
            name: this.themes[key].name,
            colors: this.themes[key].colors
        }));
    }
    
    // Public API methods
    setTheme(themeName) {
        this.applyTheme(themeName);
    }
    
    addCustomTheme(name, themeData) {
        this.themes[name] = themeData;
        this.setupThemeButtons();
    }
    
    removeCustomTheme(name) {
        if (this.themes[name] && Object.keys(this.themes).length > 1) {
            delete this.themes[name];
            if (this.currentTheme === name) {
                this.applyTheme('neon');
            }
            this.setupThemeButtons();
        }
    }
}

// Add CSS animations for theme effects
const themeAnimationCSS = `
    @keyframes theme-flash {
        0% { 
            transform: scale(1); 
            filter: brightness(1) saturate(1);
        }
        50% { 
            transform: scale(1.02); 
            filter: brightness(1.2) saturate(1.1);
        }
        100% { 
            transform: scale(1); 
            filter: brightness(1) saturate(1);
        }
    }
    
    @keyframes theme-burst-particle {
        0% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
        }
        100% {
            transform: translate(calc(-50% + var(--end-x)), calc(-50% + var(--end-y))) scale(0);
            opacity: 0;
        }
    }
    
    .theme-transitioning {
        transition: all 0.5s ease !important;
    }
    
    .theme-transitioning * {
        transition: color 0.5s ease, background-color 0.5s ease, border-color 0.5s ease, box-shadow 0.5s ease !important;
    }
`;

// Inject theme animation CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = themeAnimationCSS;
document.head.appendChild(styleSheet);

// Auto-initialize theme manager
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}