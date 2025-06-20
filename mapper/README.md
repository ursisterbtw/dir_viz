# Directory Mapper

A Rust tool that generates an interactive SVG visualization of your directory structure. The visualization features a neon-themed design with collapsible directory nodes and glowing connectors.

## Features

- Interactive SVG output with collapsible directories
- Neon-themed visual design with glowing effects
- Filters out common unwanted directories (target, gen, hidden folders)
- Alphabetically sorted entries with directories first
- Error handling for invalid paths and IO operations
- Responsive layout with automatic spacing

## Usage

```bash
cargo run
```

This will generate a `repo_map.svg` file in the current directory, containing an interactive visualization of your directory structure.

## Visualization Features

- **Directory Nodes**: Shown in neon cyan (#00fff7)
- **File Nodes**: Shown in neon green (#39ff14)
- **Interactive**: Click on directory nodes to collapse/expand their contents
- **Visual Effects**: Glowing borders and text for better visibility
- **Curved Connectors**: Smooth Bezier curves connecting nodes

## Development

### Project Structure

- `main.rs`: Core implementation
- `svg_defs.svg`: SVG filter and style definitions
- `svg_script.js`: Interactive behavior JavaScript

### Building

```bash
cargo build --release
```

### Running Tests

```bash
cargo test
```

## License

MIT License
