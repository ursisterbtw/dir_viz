# 👀 dir_viz 👀

**A collection of CLI tools that transform directory structures into stunning visual diagrams!**

This project currently contains 3 tools for visualizing directory structures and similar tasks:

- **flowcharter.py**: Generates animated SVG flowcharts of your directory structure with neon effects and glowing animations.
- **mermaider.py**: Creates clean Mermaid diagrams of your directory structure for documentation and presentations.
- **repomixr**: A Python script (located in the `repomixr/` directory) that processes GitHub repositories. It clones specified repositories, runs the `npx repomix` command (a Node.js tool) to analyze their content (excluding many common non-source files like documentation, binaries, and build artifacts), and saves the resulting `repomix-output.xml` to a configurable output directory (default `repomixd/`). It supports processing multiple repositories concurrently and can take input from command-line arguments or a source file.

All tools feature performance optimizations including memory-efficient scanning, cached operations, and smart exclusion patterns for build/cache folders.

## Features

### Flowcharter (flowcharter.py)

- **Animated SVG Output:** Creates eye-popping flowcharts with glowing nodes, pulsing edges, and smooth animations
- **Neon Theming:** Cyberpunk-inspired color schemes with customizable palettes
- **Performance Optimized:** Memory-efficient scanning with cached font loading and node generation
- **Graphviz Integration:** Robust layouts using pydot and Graphviz
- **Multiple Formats:** Outputs both DOT and animated/static SVG files

### Mermaider (mermaider.py)  

- **Mermaid Diagrams:** Generates clean, documentation-ready Mermaid syntax
- **Smart Formatting:** Automatic node styling and hierarchy visualization
- **Configurable Output:** Customizable styling and structure options

### Repomixr (repomixr/repomixr.py)

- **Batch Repo Analysis:** Clones one or more GitHub repositories, removes git metadata, and runs npx repomix to generate summary XML files.
- **Flexible Input:** Accepts repo names as CLI arguments or from a text file (SOURCE_REPOS_TXT_FILE).
- **Automated Cleanup:** Cleans up all temporary files and supports parallel processing for speed.
- **Custom Output:** Stores XML reports in a configurable output directory (OUTPUT_DIR).
- **Authentication Support:** Can use a GitHub token for private repos via GitHub CLI.

### Shared Features

- **Smart Exclusions:** Automatically filters out build folders, caches, and common artifacts
- **Parallel Processing:** Optional multi-threaded directory scanning for large projects
- **Modular Architecture:** Clean, maintainable codebase with shared utilities
- **Flexible Configuration:** Centralized settings for colors, patterns, and behavior

### Workflow Guidance

For optimal results run the workflow/ prompts in sequential order. This ensures that each step correctly builds upon the previous ones, leading to the most effective and accurate outcomes.

## Example Output

**Flowcharter** generates animated SVGs with glowing effects:

![Flowcharter Example](./flowchart.svg)

- Nodes pulse and glow with neon colors
- Edges animate with flowing dashes
- Hover effects for interactive exploration
- Embedded fonts for consistent rendering

**Mermaider** creates clean Mermaid diagrams:

- Perfect for documentation and README files
- Compatible with GitHub, GitLab, and Mermaid Live
- Hierarchical structure with proper styling

## Installation & Setup

**Prerequisites:**

- Python 3.6+
- Graphviz (system package)

**Install system dependencies:**

```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Windows (using chocolatey)
choco install graphviz
```

**Install Python dependencies:**

```bash
pip install pydot tqdm
```

**Quick start:**

```bash
# Generate animated SVG flowchart
python flowcharter.py /path/to/your/project

# Generate Mermaid diagram
python mermaider.py /path/to/your/project -o project.mermaid
```

## Usage

### Flowcharter (Animated SVG)

```bash
# Basic usage - generates flowchart.svg in current directory
python flowcharter.py /path/to/your/project

# Advanced options
python flowcharter.py /path/to/your/project \
  -o mychart.svg \
  --dot-output mychart.dot \
  --parallel \
  --max-depth 8 \
  --open

# Static SVG (no animation)
python flowcharter.py /path/to/your/project --no-animation

# Quiet mode for scripts
python flowcharter.py /path/to/your/project --quiet
```

### Mermaider (Mermaid Diagrams)

```bash
# Basic usage - generates project_structure.mermaid
python mermaider.py /path/to/your/project

# Custom output file
python mermaider.py /path/to/your/project -o project.mermaid

# With depth limit
python mermaider.py /path/to/your/project --max-depth 5
```
### Repomixr

```bash
# Analyze a repo
python repomixr/repomixr.py bitcoin/bitcoin

# Analyze multiple repos from a file
export SOURCE_REPOS_TXT_FILE=my_repos.txt
python repomixr/repomixr.py
```

**Viewing Results:**

- SVG files: Open in any modern browser to see animations
- Mermaid files: Copy content to [mermaid.live](https://mermaid.live) or use in documentation

## How It Works

### Flowcharter Process

1. **Scans** directory recursively with memory-efficient generators
2. **Creates** DOT graph using pydot with optimized node generation
3. **Applies** neon color schemes and styling
4. **Generates** SVG with embedded CSS animations
5. **Adds** glowing effects, pulsing nodes, and animated edges

### Mermaider Process

1. **Traverses** directory structure with smart exclusions
2. **Builds** hierarchical node relationships
3. **Applies** Mermaid syntax formatting
4. **Outputs** clean diagram code ready for documentation

## Customization

The tools use a modular configuration system:

- **Color schemes**: Modify `NEON_COLORS` and color palettes in the source
- **Exclusion patterns**: Update `DEFAULT_EXCLUDE_DIRS` for different project types
- **Animation settings**: Adjust CSS animations in the SVG generation
- **Mermaid styling**: Customize node shapes and styling in Mermaid output

## Dependencies

- **Python 3.6+**
- **System**: `graphviz` package
- **Python packages**: `pydot`, `tqdm`

## Project Structure

```text
directory-visualization-tools/
├── flowcharter.py              # Animated SVG flowchart generator
├── mermaider.py               # Mermaid diagram generator  
├── repomixr/                  # Repository analysis and management tool
├── config/                    # Configuration modules
│   ├── __init__.py           #   Shared constants and imports
│   ├── mermaid.py            #   Mermaid-specific settings
│   └── visualization.py      #   Color schemes and SVG settings
├── utils/                     # Shared utilities
│   ├── __init__.py           #   Common functions and classes
│   ├── cli_common.py         #   CLI argument handling
│   ├── directory_scanner.py  #   Optimized directory traversal
│   └── file_operations.py    #   Safe file I/O operations
└── README.md                  # This file
```

## Tool Details

### `flowcharter.py`

**Generates animated SVG flowcharts with neon effects**

**Command line options:**

```bash
python flowcharter.py <directory> [options]
  -o, --output FILE         Output SVG file (default: flowchart.svg)
  --dot-output FILE         Output DOT file (default: flowchart.dot)  
  --no-animation           Generate static SVG
  --parallel               Use parallel processing
  --max-depth N            Limit directory depth
  --quiet                  Suppress progress output
  --open                   Open result in browser
```

### `mermaider.py`  

**Creates clean Mermaid diagrams for documentation**

**Command line options:**

```bash
python mermaider.py <directory> [options]
  -o, --output FILE         Output Mermaid file
  --max-depth N            Limit directory depth
  --quiet                  Suppress progress output
```

## Performance Features

- **Memory Efficient**: Generator-based directory scanning
- **Cached Operations**: Font loading and node generation with LRU caching  
- **Smart Exclusions**: Pre-compiled regex patterns for common build/cache folders
- **Parallel Processing**: Optional multi-threaded scanning for large projects
- **Optimized Rendering**: Efficient SVG generation with embedded animations

## Contributing

Contributions are welcome! Feel free to:

- Report bugs or request features via issues
- Submit pull requests for improvements
- Share examples of generated visualizations
- Suggest new output formats or styling options

## Author

sister

---

> "Transform your directory structures into visual masterpieces!"
