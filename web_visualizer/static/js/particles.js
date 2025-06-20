/**
 * Particle System for Background Effects
 * Creates an animated particle field with neon-style effects
 */

class ParticleSystem {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.mousePosition = { x: 0, y: 0 };
        this.isMouseInside = false;
        this.animationId = null;
        
        // Configuration
        this.config = {
            particleCount: 80,
            particleSize: { min: 1, max: 3 },
            speed: { min: 0.3, max: 1.2 },
            colors: [
                'rgba(0, 255, 153, 0.6)',  // neon-primary
                'rgba(0, 255, 204, 0.4)',  // neon-secondary
                'rgba(51, 204, 255, 0.5)', // neon-blue
                'rgba(255, 0, 204, 0.3)',  // neon-accent
                'rgba(255, 255, 0, 0.4)'   // neon-warning
            ],
            connectionDistance: 150,
            connectionOpacity: 0.15,
            mouseInfluenceRadius: 200,
            mouseInfluenceStrength: 0.3,
            glowEffect: true,
            pulsing: true
        };
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.start();
    }
    
    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.zIndex = '-1';
        this.canvas.style.pointerEvents = 'none';
        
        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);
        
        this.resize();
    }
    
    createParticles() {
        this.particles = [];
        
        for (let i = 0; i < this.config.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * this.config.speed.max,
                vy: (Math.random() - 0.5) * this.config.speed.max,
                size: this.config.particleSize.min + 
                      Math.random() * (this.config.particleSize.max - this.config.particleSize.min),
                color: this.config.colors[Math.floor(Math.random() * this.config.colors.length)],
                originalColor: null,
                opacity: 0.3 + Math.random() * 0.7,
                pulseSpeed: 0.02 + Math.random() * 0.03,
                pulsePhase: Math.random() * Math.PI * 2,
                connections: []
            });
            
            // Store original color for mouse interaction
            this.particles[this.particles.length - 1].originalColor = 
                this.particles[this.particles.length - 1].color;
        }
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => this.resize());
        
        document.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mousePosition.x = e.clientX - rect.left;
            this.mousePosition.y = e.clientY - rect.top;
        });
        
        document.addEventListener('mouseenter', () => {
            this.isMouseInside = true;
        });
        
        document.addEventListener('mouseleave', () => {
            this.isMouseInside = false;
        });
        
        // Theme change listener
        document.addEventListener('themeChanged', (e) => {
            this.updateColorsForTheme(e.detail.theme);
        });
        
        // Performance optimization - pause when tab is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
            } else {
                this.resume();
            }
        });
    }
    
    updateColorsForTheme(theme) {
        const themeColors = {
            neon: [
                'rgba(0, 255, 153, 0.6)',
                'rgba(0, 255, 204, 0.4)',
                'rgba(51, 204, 255, 0.5)',
                'rgba(255, 0, 204, 0.3)',
                'rgba(255, 255, 0, 0.4)'
            ],
            cyber: [
                'rgba(0, 255, 255, 0.6)',
                'rgba(0, 128, 255, 0.4)',
                'rgba(128, 0, 255, 0.5)',
                'rgba(255, 0, 128, 0.3)',
                'rgba(0, 255, 128, 0.4)'
            ],
            matrix: [
                'rgba(0, 255, 0, 0.6)',
                'rgba(128, 255, 0, 0.4)',
                'rgba(255, 255, 0, 0.5)',
                'rgba(0, 255, 128, 0.3)',
                'rgba(128, 255, 128, 0.4)'
            ],
            synthwave: [
                'rgba(255, 0, 128, 0.6)',
                'rgba(255, 128, 0, 0.4)',
                'rgba(255, 255, 0, 0.5)',
                'rgba(255, 0, 255, 0.3)',
                'rgba(128, 0, 255, 0.4)'
            ]
        };
        
        this.config.colors = themeColors[theme] || themeColors.neon;
        
        // Update existing particles
        this.particles.forEach(particle => {
            particle.color = this.config.colors[Math.floor(Math.random() * this.config.colors.length)];
            particle.originalColor = particle.color;
        });
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Adjust particle positions if canvas got smaller
        this.particles.forEach(particle => {
            if (particle.x > this.canvas.width) particle.x = this.canvas.width;
            if (particle.y > this.canvas.height) particle.y = this.canvas.height;
        });
    }
    
    updateParticle(particle, deltaTime) {
        // Apply base movement
        particle.x += particle.vx * deltaTime;
        particle.y += particle.vy * deltaTime;
        
        // Boundary checking with wrapping
        if (particle.x < 0) particle.x = this.canvas.width;
        if (particle.x > this.canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = this.canvas.height;
        if (particle.y > this.canvas.height) particle.y = 0;
        
        // Mouse interaction
        if (this.isMouseInside) {
            const dx = this.mousePosition.x - particle.x;
            const dy = this.mousePosition.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < this.config.mouseInfluenceRadius) {
                const force = (this.config.mouseInfluenceRadius - distance) / 
                             this.config.mouseInfluenceRadius;
                const angle = Math.atan2(dy, dx);
                
                // Attract particles to mouse
                particle.vx += Math.cos(angle) * force * this.config.mouseInfluenceStrength * deltaTime;
                particle.vy += Math.sin(angle) * force * this.config.mouseInfluenceStrength * deltaTime;
                
                // Enhance color near mouse
                const intensity = Math.min(1, force * 2);
                particle.color = this.enhanceColor(particle.originalColor, intensity);
                particle.size = particle.size * (1 + force * 0.5);
            } else {
                // Reset to original state
                particle.color = particle.originalColor;
                particle.vx *= 0.98; // Slight damping
                particle.vy *= 0.98;
            }
        }
        
        // Pulsing effect
        if (this.config.pulsing) {
            particle.pulsePhase += particle.pulseSpeed * deltaTime;
            particle.opacity = 0.3 + 0.4 * (1 + Math.sin(particle.pulsePhase)) / 2;
        }
        
        // Update connections
        this.updateConnections(particle);
    }
    
    updateConnections(particle) {
        particle.connections = [];
        
        this.particles.forEach(otherParticle => {
            if (particle === otherParticle) return;
            
            const dx = particle.x - otherParticle.x;
            const dy = particle.y - otherParticle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < this.config.connectionDistance) {
                const opacity = this.config.connectionOpacity * 
                              (1 - distance / this.config.connectionDistance);
                
                particle.connections.push({
                    particle: otherParticle,
                    opacity: opacity
                });
            }
        });
    }
    
    enhanceColor(color, intensity) {
        // Extract RGBA values
        const matches = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+),\\s*([\\d.]+)\\)/);
        if (!matches) return color;
        
        const [, r, g, b, a] = matches;
        const newA = Math.min(1, parseFloat(a) + intensity * 0.3);
        
        return `rgba(${r}, ${g}, ${b}, ${newA})`;
    }
    
    drawParticle(particle) {
        this.ctx.save();
        
        // Set up glow effect
        if (this.config.glowEffect) {
            this.ctx.shadowBlur = 20;
            this.ctx.shadowColor = particle.color;
        }
        
        // Draw particle
        this.ctx.globalAlpha = particle.opacity;
        this.ctx.fillStyle = particle.color;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Enhanced glow for larger particles
        if (particle.size > 2) {
            this.ctx.globalAlpha = particle.opacity * 0.3;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.restore();
    }
    
    drawConnections(particle) {
        particle.connections.forEach(connection => {
            this.ctx.save();
            
            this.ctx.globalAlpha = connection.opacity;
            this.ctx.strokeStyle = particle.color;
            this.ctx.lineWidth = 1;
            
            // Add glow to connections
            if (this.config.glowEffect) {
                this.ctx.shadowBlur = 5;
                this.ctx.shadowColor = particle.color;
            }
            
            this.ctx.beginPath();
            this.ctx.moveTo(particle.x, particle.y);
            this.ctx.lineTo(connection.particle.x, connection.particle.y);
            this.ctx.stroke();
            
            this.ctx.restore();
        });
    }
    
    render(deltaTime) {
        // Clear canvas with slight trail effect for motion blur
        this.ctx.fillStyle = 'rgba(10, 10, 10, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.particles.forEach(particle => {
            this.updateParticle(particle, deltaTime);
            this.drawConnections(particle);
            this.drawParticle(particle);
        });
    }
    
    animate(currentTime) {
        if (!this.lastTime) this.lastTime = currentTime;
        const deltaTime = Math.min((currentTime - this.lastTime) / 16.67, 2); // Cap at 2x speed
        this.lastTime = currentTime;
        
        this.render(deltaTime);
        
        this.animationId = requestAnimationFrame((time) => this.animate(time));
    }
    
    start() {
        if (!this.animationId) {
            this.animationId = requestAnimationFrame((time) => this.animate(time));
        }
    }
    
    pause() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    resume() {
        if (!this.animationId) {
            this.lastTime = null; // Reset timing
            this.start();
        }
    }
    
    destroy() {
        this.pause();
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        this.particles = [];
        
        // Remove event listeners
        window.removeEventListener('resize', this.resize);
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseenter', this.handleMouseEnter);
        document.removeEventListener('mouseleave', this.handleMouseLeave);
    }
    
    // Public methods for external control
    setParticleCount(count) {
        this.config.particleCount = Math.max(10, Math.min(200, count));
        this.createParticles();
    }
    
    setEffectIntensity(intensity) {
        const normalizedIntensity = Math.max(0, Math.min(1, intensity));
        this.config.connectionOpacity = 0.15 * normalizedIntensity;
        this.config.mouseInfluenceStrength = 0.5 * normalizedIntensity;
        
        if (normalizedIntensity < 0.3) {
            this.config.glowEffect = false;
            this.config.pulsing = false;
        } else {
            this.config.glowEffect = true;
            this.config.pulsing = true;
        }
    }
    
    toggleEffect(effectName, enabled) {
        switch (effectName) {
            case 'glow':
                this.config.glowEffect = enabled;
                break;
            case 'pulsing':
                this.config.pulsing = enabled;
                break;
            case 'connections':
                this.config.connectionDistance = enabled ? 150 : 0;
                break;
        }
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (!prefersReducedMotion) {
        window.particleSystem = new ParticleSystem('particle-background');
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParticleSystem;
}