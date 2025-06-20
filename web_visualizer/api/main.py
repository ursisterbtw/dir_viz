"""Main FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from ..config import config
from .routes import router
from .middleware import setup_middleware

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    log.info("Starting Directory Visualizer Web API")
    log.info(f"Debug mode: {config.debug}")
    log.info(f"Static files: {config.static_dir}")
    log.info(f"Templates: {config.template_dir}")
    
    # Create directories if they don't exist
    config.static_dir.mkdir(parents=True, exist_ok=True)
    config.template_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    log.info("Shutting down Directory Visualizer Web API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Directory Visualizer Web API",
        description="Interactive web-based directory visualization with D3.js",
        version="1.0.0",
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
        openapi_url="/openapi.json" if config.debug else None,
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include API routes
    app.include_router(router)
    
    # Static file serving
    static_path = config.static_dir
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Serve main application
    @app.get("/", response_class=HTMLResponse)
    async def serve_app():
        """Serve the main web application."""
        template_path = config.template_dir / "index.html"
        
        if template_path.exists():
            return HTMLResponse(content=template_path.read_text(), status_code=200)
        else:
            # Return a basic HTML page if template doesn't exist
            return HTMLResponse(content=get_default_html(), status_code=200)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers."""
        return {"status": "healthy", "service": "dir_viz_web"}
    
    
    return app


def get_default_html() -> str:
    """Get default HTML content when template is not available."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Directory Visualizer</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #121212;
            color: #ffffff;
            overflow: hidden;
        }
        
        .header {
            background: #1a1a1a;
            padding: 1rem;
            border-bottom: 2px solid #00ff99;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #00ff99;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .path-input {
            padding: 0.5rem;
            background: #2a2a2a;
            border: 1px solid #333;
            color: #fff;
            border-radius: 4px;
            min-width: 300px;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            background: #00ff99;
            color: #000;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: #00ccff;
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }
        
        .main-content {
            height: calc(100vh - 80px);
            display: flex;
        }
        
        .sidebar {
            width: 300px;
            background: #1a1a1a;
            border-right: 1px solid #333;
            padding: 1rem;
            overflow-y: auto;
        }
        
        .visualization {
            flex: 1;
            position: relative;
            background: radial-gradient(circle at center, #1a1a1a 0%, #121212 100%);
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid #333;
            border-top: 3px solid #00ff99;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .node {
            cursor: pointer;
        }
        
        .node circle {
            fill: #00ff99;
            stroke: #fff;
            stroke-width: 2px;
            transition: all 0.3s ease;
        }
        
        .node:hover circle {
            fill: #00ccff;
            stroke-width: 3px;
            filter: drop-shadow(0 0 8px #00ccff);
        }
        
        .node text {
            font: 12px sans-serif;
            fill: #fff;
            text-anchor: start;
            dominant-baseline: middle;
        }
        
        .link {
            fill: none;
            stroke: #32CD32;
            stroke-width: 2px;
            stroke-opacity: 0.6;
        }
        
        .error {
            color: #ff4444;
            padding: 1rem;
            background: #2a1a1a;
            border: 1px solid #ff4444;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .stats {
            background: #2a2a2a;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        
        .stats h3 {
            margin: 0 0 0.5rem 0;
            color: #00ff99;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin: 0.25rem 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">📁 Directory Visualizer</div>
        <div class="controls">
            <input type="text" id="pathInput" class="path-input" placeholder="Enter directory path..." value="/home/sistr/Projects/dir_viz">
            <button id="scanBtn" class="btn">Scan Directory</button>
            <button id="exportBtn" class="btn" disabled>Export</button>
        </div>
    </div>
    
    <div class="main-content">
        <div class="sidebar">
            <div id="stats" class="stats" style="display: none;">
                <h3>Directory Stats</h3>
                <div class="stat-item">
                    <span>Files:</span>
                    <span id="fileCount">0</span>
                </div>
                <div class="stat-item">
                    <span>Directories:</span>
                    <span id="dirCount">0</span>
                </div>
                <div class="stat-item">
                    <span>Max Depth:</span>
                    <span id="maxDepth">5</span>
                </div>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            
            <div>
                <h3>Instructions</h3>
                <ul>
                    <li>Enter a directory path and click "Scan Directory"</li>
                    <li>Use mouse wheel to zoom in/out</li>
                    <li>Click and drag to pan around</li>
                    <li>Click on nodes to expand/collapse</li>
                    <li>Hover over nodes for details</li>
                </ul>
            </div>
        </div>
        
        <div class="visualization">
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <div>Scanning directory...</div>
            </div>
            <svg id="visualization"></svg>
        </div>
    </div>

    <script>
        // Application state
        let currentTreeData = null;
        let svg, g, root;
        
        // D3 setup
        const width = window.innerWidth - 300;
        const height = window.innerHeight - 80;
        
        svg = d3.select("#visualization")
            .attr("width", width)
            .attr("height", height);
            
        g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
            
        svg.call(zoom);
        
        // Tree layout
        const treeLayout = d3.tree().size([height - 100, width - 100]);
        
        // Event listeners
        document.getElementById('scanBtn').addEventListener('click', scanDirectory);
        document.getElementById('pathInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') scanDirectory();
        });
        
        async function scanDirectory() {
            const path = document.getElementById('pathInput').value.trim();
            if (!path) return;
            
            showLoading(true);
            hideError();
            
            try {
                const response = await fetch('/api/scan-directory', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ path, max_depth: 5 })
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.detail || 'Failed to scan directory');
                }
                
                if (result.success) {
                    currentTreeData = result.tree;
                    updateStats(result.metadata);
                    visualizeTree(result.tree);
                    document.getElementById('exportBtn').disabled = false;
                } else {
                    throw new Error(result.error || 'Scan failed');
                }
                
            } catch (error) {
                showError(error.message);
            } finally {
                showLoading(false);
            }
        }
        
        function visualizeTree(data) {
            // Clear previous visualization
            g.selectAll("*").remove();
            
            // Create hierarchy
            root = d3.hierarchy(data);
            
            // Position nodes
            treeLayout(root);
            
            // Create links
            const links = g.selectAll(".link")
                .data(root.links())
                .enter().append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y + 50)
                    .y(d => d.x + 50));
            
            // Create nodes
            const nodes = g.selectAll(".node")
                .data(root.descendants())
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${d.y + 50},${d.x + 50})`);
            
            // Add circles
            nodes.append("circle")
                .attr("r", 6)
                .style("fill", d => d.data.type === "directory" ? "#00ff99" : "#ff6b6b");
            
            // Add labels
            nodes.append("text")
                .attr("dx", 12)
                .attr("dy", 3)
                .text(d => d.data.name);
            
            // Center the view
            const bounds = g.node().getBBox();
            const fullWidth = width;
            const fullHeight = height;
            const widthScale = fullWidth / bounds.width;
            const heightScale = fullHeight / bounds.height;
            const scale = Math.min(widthScale, heightScale) * 0.8;
            
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
                    .translate(fullWidth / 2, fullHeight / 2)
                    .scale(scale)
                    .translate(-bounds.x - bounds.width / 2, -bounds.y - bounds.height / 2)
            );
        }
        
        function updateStats(metadata) {
            document.getElementById('fileCount').textContent = metadata.file_count;
            document.getElementById('dirCount').textContent = metadata.dir_count;
            document.getElementById('maxDepth').textContent = metadata.max_depth;
            document.getElementById('stats').style.display = 'block';
        }
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'flex' : 'none';
            document.getElementById('scanBtn').disabled = show;
        }
        
        function showError(message) {
            const errorEl = document.getElementById('error');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        // Handle window resize
        window.addEventListener('resize', () => {
            const newWidth = window.innerWidth - 300;
            const newHeight = window.innerHeight - 80;
            
            svg.attr("width", newWidth).attr("height", newHeight);
            treeLayout.size([newHeight - 100, newWidth - 100]);
            
            if (currentTreeData) {
                visualizeTree(currentTreeData);
            }
        });
    </script>
</body>
</html>'''