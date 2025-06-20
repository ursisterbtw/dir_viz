/**
 * Advanced D3.js Visualization System
 * Multiple layout types with smooth animations and interactive features
 */

class VisualizationEngine {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.svg = null;
        this.g = null;
        this.data = null;
        this.currentLayout = 'tree';
        this.width = 0;
        this.height = 0;
        this.animationDuration = 900;
        this.maxNodes = 1000;
        
        // Zoom and pan
        this.zoom = null;
        this.currentTransform = { x: 0, y: 0, k: 1 };
        
        // Color schemes for different file types
        this.fileTypeColors = {
            'js': '#f7df1e',
            'ts': '#3178c6',
            'py': '#3776ab',
            'html': '#e34f26',
            'css': '#1572b6',
            'json': '#000000',
            'md': '#083fa1',
            'yml': '#cb171e',
            'yaml': '#cb171e',
            'xml': '#005faf',
            'txt': '#666666',
            'default': '#00ff99'
        };
        
        // Layout configurations
        this.layouts = {
            tree: this.createTreeLayout.bind(this),
            force: this.createForceLayout.bind(this),
            radial: this.createRadialLayout.bind(this),
            treemap: this.createTreemapLayout.bind(this),
            sunburst: this.createSunburstLayout.bind(this),
            galaxy: this.createGalaxyLayout.bind(this)
        };
        
        this.init();
    }
    
    init() {
        this.setupSVG();
        this.setupZoom();
        this.setupFilters();
        this.setupEventListeners();
        this.resize();
    }
    
    setupSVG() {
        // Clear existing content
        this.container.selectAll('*').remove();
        
        this.svg = this.container
            .append('svg')
            .attr('class', 'visualization-svg')
            .style('width', '100%')
            .style('height', '100%');
            
        // Create main group for transformations
        this.g = this.svg.append('g').attr('class', 'main-group');
        
        // Create layers
        this.g.append('g').attr('class', 'links-layer');
        this.g.append('g').attr('class', 'nodes-layer');
        this.g.append('g').attr('class', 'labels-layer');
        this.g.append('g').attr('class', 'effects-layer');
    }
    
    setupZoom() {
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.currentTransform = event.transform;
                this.g.attr('transform', event.transform);
                this.updateZoomDependentElements();
            });
            
        this.svg.call(this.zoom);
    }
    
    setupFilters() {
        const defs = this.svg.append('defs');
        
        // Glow filter
        const glowFilter = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-20%')
            .attr('y', '-20%')
            .attr('width', '140%')
            .attr('height', '140%');
            
        glowFilter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');
            
        const feMerge = glowFilter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
        
        // Pulse filter
        const pulseFilter = defs.append('filter')
            .attr('id', 'pulse')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');
            
        pulseFilter.append('feGaussianBlur')
            .attr('stdDeviation', '0')
            .attr('result', 'pulsedBlur')
            .append('animate')
            .attr('attributeName', 'stdDeviation')
            .attr('values', '0;3;0')
            .attr('dur', '2s')
            .attr('repeatCount', 'indefinite');
            
        // Gradient definitions
        const gradient = defs.append('radialGradient')
            .attr('id', 'nodeGradient')
            .attr('cx', '30%')
            .attr('cy', '30%');
            
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#ffffff')
            .attr('stop-opacity', 0.3);
            
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#000000')
            .attr('stop-opacity', 0.1);
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => this.resize());
        
        // Theme change listener
        document.addEventListener('themeChanged', (e) => {
            this.updateColorsForTheme(e.detail);
        });
        
        // Layout change listener
        document.addEventListener('layoutChanged', (e) => {
            this.setLayout(e.detail.layout);
        });
        
        // Settings change listeners
        document.addEventListener('settingsChanged', (e) => {
            this.updateSettings(e.detail);
        });
    }
    
    resize() {
        const rect = this.container.node().getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        
        this.svg
            .attr('width', this.width)
            .attr('height', this.height);
            
        if (this.data) {
            this.render(this.data, false); // Re-render without animation
        }
    }
    
    // Main rendering method
    render(data, animate = true) {
        if (!data) return;
        
        this.data = data;
        this.animationDuration = animate ? 900 : 0;
        
        // Process data for current layout
        const processedData = this.preprocessData(data);
        
        // Apply current layout
        const layoutFunction = this.layouts[this.currentLayout];
        if (layoutFunction) {
            layoutFunction(processedData);
        } else {
            console.warn(`Layout '${this.currentLayout}' not found, falling back to tree`);
            this.currentLayout = 'tree';
            this.layouts.tree(processedData);
        }
        
        this.updateStats(processedData);
    }
    
    preprocessData(data) {
        // Flatten the hierarchy for easier processing
        const nodes = [];
        const links = [];
        
        const traverse = (node, parent = null, depth = 0) => {
            if (nodes.length >= this.maxNodes) return;
            
            const processedNode = {
                id: node.id,
                name: node.name,
                type: node.type,
                path: node.path,
                size: node.size || 0,
                fileCount: node.fileCount || 0,
                dirCount: node.dirCount || 0,
                depth: depth,
                parent: parent,
                children: [],
                originalData: node
            };
            
            nodes.push(processedNode);
            
            if (parent) {
                links.push({
                    source: parent,
                    target: processedNode
                });
                parent.children.push(processedNode);
            }
            
            if (node.children && node.children.length > 0) {
                node.children.forEach(child => {
                    traverse(child, processedNode, depth + 1);
                });
            }
        };
        
        traverse(data);
        
        return { nodes, links, root: nodes[0] };
    }
    
    // Layout implementations
    createTreeLayout(data) {
        const treeLayout = d3.tree()
            .size([this.height - 100, this.width - 200])
            .separation((a, b) => a.parent === b.parent ? 1 : 2);
            
        const hierarchy = d3.hierarchy(data.root, d => d.children);
        const treeData = treeLayout(hierarchy);
        
        // Transform coordinates
        treeData.descendants().forEach(d => {
            d.y = d.depth * 180 + 100;
        });
        
        this.renderNodes(treeData.descendants());
        this.renderLinks(treeData.links());
    }
    
    createForceLayout(data) {
        const simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.links)
                .id(d => d.id)
                .distance(d => {
                    const baseDistance = 50;
                    const sizeMultiplier = Math.log(1 + (d.target.fileCount || 1)) * 10;
                    return baseDistance + sizeMultiplier;
                })
                .strength(0.5))
            .force('charge', d3.forceManyBody()
                .strength(d => {
                    const baseStrength = -100;
                    const sizeMultiplier = Math.log(1 + (d.fileCount || 1));
                    return baseStrength * sizeMultiplier;
                }))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide()
                .radius(d => this.getNodeRadius(d) + 5));
        
        // Store simulation for updates
        this.simulation = simulation;
        
        const nodes = this.renderNodes(data.nodes);
        const links = this.renderLinks(data.links);
        
        simulation.on('tick', () => {
            links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
                
            nodes
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });
        
        // Add drag behavior
        const drag = d3.drag()
            .on('start', (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
            
        nodes.call(drag);
    }
    
    createRadialLayout(data) {
        const radius = Math.min(this.width, this.height) / 2 - 100;
        
        const tree = d3.tree()
            .size([2 * Math.PI, radius])
            .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth);
            
        const hierarchy = d3.hierarchy(data.root, d => d.children);
        const treeData = tree(hierarchy);
        
        // Convert polar to cartesian coordinates
        treeData.descendants().forEach(d => {
            d.x = d.y * Math.cos(d.x - Math.PI / 2) + this.width / 2;
            d.y = d.y * Math.sin(d.x - Math.PI / 2) + this.height / 2;
        });
        
        this.renderNodes(treeData.descendants());
        this.renderLinks(treeData.links());
    }
    
    createTreemapLayout(data) {
        const treemap = d3.treemap()
            .size([this.width - 100, this.height - 100])
            .padding(2)
            .round(true);
            
        const hierarchy = d3.hierarchy(data.root, d => d.children)
            .sum(d => d.size || 1)
            .sort((a, b) => b.value - a.value);
            
        const treemapData = treemap(hierarchy);
        
        this.renderTreemapNodes(treemapData.descendants());
    }
    
    createSunburstLayout(data) {
        const radius = Math.min(this.width, this.height) / 2 - 10;
        
        const partition = d3.partition()
            .size([2 * Math.PI, radius]);
            
        const hierarchy = d3.hierarchy(data.root, d => d.children)
            .sum(d => d.size || 1);
            
        const partitionData = partition(hierarchy);
        
        this.renderSunburstNodes(partitionData.descendants());
    }
    
    createGalaxyLayout(data) {
        // Custom galaxy-style layout with spiral arms
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const maxRadius = Math.min(this.width, this.height) / 2 - 50;
        
        // Create spiral arms
        const spiralArms = 3;
        const spiralTightness = 0.2;
        
        data.nodes.forEach((node, index) => {
            if (index === 0) {
                // Root at center
                node.x = centerX;
                node.y = centerY;
            } else {
                const armIndex = index % spiralArms;
                const armAngle = (armIndex / spiralArms) * 2 * Math.PI;
                const spiralIndex = Math.floor(index / spiralArms);
                
                const radius = (spiralIndex / data.nodes.length) * maxRadius;
                const angle = armAngle + radius * spiralTightness;
                
                // Add some randomness for natural look
                const randomRadius = radius + (Math.random() - 0.5) * 20;
                const randomAngle = angle + (Math.random() - 0.5) * 0.5;
                
                node.x = centerX + randomRadius * Math.cos(randomAngle);
                node.y = centerY + randomRadius * Math.sin(randomAngle);
            }
        });
        
        this.renderNodes(data.nodes);
        this.renderLinks(data.links);
        
        // Add rotating animation
        this.addGalaxyRotation();
    }
    
    // Node rendering methods
    renderNodes(nodes) {
        const nodeSelection = this.g.select('.nodes-layer')
            .selectAll('.node')
            .data(nodes, d => d.data ? d.data.id : d.id);
            
        // Remove exiting nodes
        nodeSelection.exit()
            .transition()
            .duration(this.animationDuration)
            .ease(d3.easeCubicOut)
            .attr('transform', 'scale(0)')
            .style('opacity', 0)
            .remove();
            
        // Add new nodes
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => {
                const x = d.x || this.width / 2;
                const y = d.y || this.height / 2;
                return `translate(${x},${y}) scale(0)`;
            })
            .style('opacity', 0);
            
        // Add circles
        nodeEnter.append('circle')
            .attr('class', 'node-circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeStrokeColor(d))
            .attr('stroke-width', 2)
            .style('filter', 'url(#glow)');
            
        // Add labels
        nodeEnter.append('text')
            .attr('class', 'node-text')
            .attr('dy', '.35em')
            .attr('text-anchor', 'middle')
            .text(d => this.getNodeLabel(d))
            .style('font-size', d => `${Math.max(8, this.getNodeRadius(d) / 3)}px`)
            .style('fill', '#ffffff')
            .style('pointer-events', 'none');
            
        // Add interaction handlers
        nodeEnter
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip())
            .on('click', (event, d) => this.handleNodeClick(event, d))
            .on('dblclick', (event, d) => this.handleNodeDoubleClick(event, d));
            
        // Update existing nodes
        const nodeUpdate = nodeEnter.merge(nodeSelection);
        
        nodeUpdate
            .transition()
            .duration(this.animationDuration)
            .ease(d3.easeCubicOut)
            .attr('transform', d => {
                const x = d.x || this.width / 2;
                const y = d.y || this.height / 2;
                return `translate(${x},${y}) scale(1)`;
            })
            .style('opacity', 1);
            
        nodeUpdate.select('circle')
            .transition()
            .duration(this.animationDuration)
            .ease(d3.easeCubicOut)
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeStrokeColor(d));
            
        return nodeUpdate;
    }
    
    renderLinks(links) {
        const linkSelection = this.g.select('.links-layer')
            .selectAll('.link')
            .data(links, d => `${d.source.data ? d.source.data.id : d.source.id}-${d.target.data ? d.target.data.id : d.target.id}`);
            
        // Remove exiting links
        linkSelection.exit()
            .transition()
            .duration(this.animationDuration)
            .ease(d3.easeCubicOut)
            .style('opacity', 0)
            .remove();
            
        // Add new links
        const linkEnter = linkSelection.enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', '#00ff99')
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.6)
            .style('opacity', 0);
            
        // Update all links
        const linkUpdate = linkEnter.merge(linkSelection);
        
        linkUpdate
            .transition()
            .duration(this.animationDuration)
            .ease(d3.easeCubicOut)
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y)
            .style('opacity', 1);
            
        return linkUpdate;
    }
    
    renderTreemapNodes(nodes) {
        const nodeSelection = this.g.select('.nodes-layer')
            .selectAll('.treemap-node')
            .data(nodes, d => d.data.id);
            
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'treemap-node');
            
        nodeEnter.append('rect')
            .attr('x', d => d.x0 + 50)
            .attr('y', d => d.y0 + 50)
            .attr('width', d => d.x1 - d.x0)
            .attr('height', d => d.y1 - d.y0)
            .attr('fill', d => this.getNodeColor(d.data))
            .attr('stroke', '#00ff99')
            .attr('stroke-width', 1)
            .style('opacity', 0.8);
            
        nodeEnter.append('text')
            .attr('x', d => (d.x0 + d.x1) / 2 + 50)
            .attr('y', d => (d.y0 + d.y1) / 2 + 50)
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .text(d => d.data.name)
            .style('font-size', '12px')
            .style('fill', '#ffffff');
            
        nodeEnter
            .on('mouseover', (event, d) => this.showTooltip(event, d.data))
            .on('mouseout', () => this.hideTooltip());
    }
    
    renderSunburstNodes(nodes) {
        const arc = d3.arc()
            .startAngle(d => d.x0)
            .endAngle(d => d.x1)
            .innerRadius(d => d.y0)
            .outerRadius(d => d.y1);
            
        const nodeSelection = this.g.select('.nodes-layer')
            .selectAll('.sunburst-node')
            .data(nodes, d => d.data.id);
            
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'sunburst-node')
            .attr('transform', `translate(${this.width / 2},${this.height / 2})`);
            
        nodeEnter.append('path')
            .attr('d', arc)
            .attr('fill', d => this.getNodeColor(d.data))
            .attr('stroke', '#00ff99')
            .attr('stroke-width', 1)
            .style('opacity', 0.8);
            
        nodeEnter
            .on('mouseover', (event, d) => this.showTooltip(event, d.data))
            .on('mouseout', () => this.hideTooltip());
    }
    
    // Utility methods
    getNodeRadius(node) {
        const data = node.data || node;
        const baseRadius = 8;
        const sizeMultiplier = Math.log(1 + (data.size || 1)) * 2;
        const childMultiplier = Math.log(1 + (data.fileCount || 1)) * 3;
        return Math.max(baseRadius, Math.min(30, baseRadius + sizeMultiplier + childMultiplier));
    }
    
    getNodeColor(node) {
        const data = node.data || node;
        
        if (data.type === 'directory') {
            return '#33ccff';
        }
        
        // Get file extension
        const extension = data.name.split('.').pop().toLowerCase();
        return this.fileTypeColors[extension] || this.fileTypeColors.default;
    }
    
    getNodeStrokeColor(node) {
        const data = node.data || node;
        return data.type === 'directory' ? '#00ff99' : '#ffffff';
    }
    
    getNodeLabel(node) {
        const data = node.data || node;
        const maxLength = 12;
        return data.name.length > maxLength ? 
            data.name.substring(0, maxLength) + '...' : 
            data.name;
    }
    
    // Animation helpers
    addGalaxyRotation() {
        const rotationSpeed = 0.01; // radians per frame
        
        const rotate = () => {
            this.g.select('.nodes-layer')
                .transition()
                .duration(100)
                .attr('transform', d => {
                    const currentTransform = d3.select(this).attr('transform') || 'rotate(0)';
                    const currentAngle = parseFloat(currentTransform.match(/rotate\\(([^)]+)\\)/)?.[1] || '0');
                    return `rotate(${currentAngle + rotationSpeed}) translate(${this.width / 2},${this.height / 2})`;
                });
                
            requestAnimationFrame(rotate);
        };
        
        // Uncomment to enable continuous rotation
        // rotate();
    }
    
    // Event handlers
    showTooltip(event, data) {
        const tooltip = d3.select('#tooltip');
        
        tooltip.select('.tooltip-name').text(data.name);
        tooltip.select('.tooltip-type').text(data.type);
        tooltip.select('.tooltip-size').text(this.formatFileSize(data.size || 0));
        tooltip.select('.tooltip-path').text(data.path);
        tooltip.select('.tooltip-child-count').text(`${data.fileCount || 0} files, ${data.dirCount || 0} dirs`);
        
        // Set icon based on type
        const icon = tooltip.select('.tooltip-icon');
        if (data.type === 'directory') {
            icon.className = 'fas fa-folder tooltip-icon';
        } else {
            icon.className = 'fas fa-file tooltip-icon';
        }
        
        tooltip
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .classed('hidden', false);
    }
    
    hideTooltip() {
        d3.select('#tooltip').classed('hidden', true);
    }
    
    handleNodeClick(event, data) {
        // Highlight clicked node
        d3.selectAll('.node-circle').style('stroke-width', 2);
        d3.select(event.currentTarget).select('.node-circle').style('stroke-width', 4);
        
        // Dispatch custom event
        const customEvent = new CustomEvent('nodeClicked', {
            detail: { node: data, event: event }
        });
        document.dispatchEvent(customEvent);
    }
    
    handleNodeDoubleClick(event, data) {
        // Zoom to node
        this.zoomToNode(data);
        
        // Dispatch custom event
        const customEvent = new CustomEvent('nodeDoubleClicked', {
            detail: { node: data, event: event }
        });
        document.dispatchEvent(customEvent);
    }
    
    // Zoom and pan utilities
    zoomToNode(node) {
        const scale = 2;
        const x = -node.x * scale + this.width / 2;
        const y = -node.y * scale + this.height / 2;
        
        this.svg.transition()
            .duration(900)
            .ease(d3.easeCubicOut)
            .call(this.zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }
    
    resetZoom() {
        this.svg.transition()
            .duration(900)
            .ease(d3.easeCubicOut)
            .call(this.zoom.transform, d3.zoomIdentity);
    }
    
    autoFit() {
        if (!this.data) return;
        
        const bounds = this.g.node().getBBox();
        const fullWidth = this.width;
        const fullHeight = this.height;
        const width = bounds.width;
        const height = bounds.height;
        const midX = bounds.x + width / 2;
        const midY = bounds.y + height / 2;
        
        if (width === 0 || height === 0) return;
        
        const scale = Math.min(fullWidth / width, fullHeight / height) * 0.9;
        const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];
        
        this.svg.transition()
            .duration(900)
            .ease(d3.easeCubicOut)
            .call(this.zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    }
    
    updateZoomDependentElements() {
        // Update text size based on zoom level
        const scale = this.currentTransform.k;
        const fontSize = Math.max(8, 12 / scale);
        
        this.g.selectAll('.node-text')
            .style('font-size', `${fontSize}px`);
    }
    
    // Settings and theme updates
    updateColorsForTheme(themeData) {
        this.fileTypeColors.default = themeData.colors.primary;
        
        // Update existing visualization
        if (this.data) {
            this.g.selectAll('.node-circle')
                .transition()
                .duration(500)
                .attr('fill', d => this.getNodeColor(d))
                .attr('stroke', d => this.getNodeStrokeColor(d));
                
            this.g.selectAll('.link')
                .transition()
                .duration(500)
                .attr('stroke', themeData.colors.primary);
        }
    }
    
    updateSettings(settings) {
        if (settings.animationDuration !== undefined) {
            this.animationDuration = settings.animationDuration;
        }
        
        if (settings.maxNodes !== undefined) {
            this.maxNodes = settings.maxNodes;
        }
        
        // Re-render if needed
        if (this.data) {
            this.render(this.data, false);
        }
    }
    
    updateStats(data) {
        // Update statistics in the UI
        document.getElementById('file-count').textContent = data.nodes.filter(n => n.type === 'file').length;
        document.getElementById('dir-count').textContent = data.nodes.filter(n => n.type === 'directory').length;
        document.getElementById('max-depth').textContent = Math.max(...data.nodes.map(n => n.depth));
        
        const totalSize = data.nodes.reduce((sum, node) => sum + (node.size || 0), 0);
        document.getElementById('total-size').textContent = this.formatFileSize(totalSize);
        
        document.getElementById('node-counter').textContent = `${data.nodes.length} nodes`;
    }
    
    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    // Public API
    setLayout(layoutName) {
        if (this.layouts[layoutName]) {
            this.currentLayout = layoutName;
            if (this.data) {
                this.render(this.data, true);
            }
        }
    }
    
    setData(data) {
        this.render(data, true);
    }
    
    exportSVG() {
        const svgNode = this.svg.node();
        const serializer = new XMLSerializer();
        return serializer.serializeToString(svgNode);
    }
    
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        this.container.selectAll('*').remove();
    }
}

// Export for global usage
window.VisualizationEngine = VisualizationEngine;