use std::error::Error;
use std::fs;
use std::io;
use std::path::Path;

/// Error type for the mapper application
#[derive(Debug)]
pub enum MapperError {
    IoError(io::Error),
    InvalidPath(String),
}

impl std::fmt::Display for MapperError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MapperError::IoError(e) => write!(f, "IO error: {e}"),
            MapperError::InvalidPath(p) => write!(f, "Invalid path: {p}"),
        }
    }
}

impl Error for MapperError {}

impl From<io::Error> for MapperError {
    fn from(err: io::Error) -> Self {
        MapperError::IoError(err)
    }
}

/// Represents a node type in the directory tree
#[derive(Debug, Clone, PartialEq)]
pub enum NodeType {
    /// Represents a directory node
    Directory,
    /// Represents a file node
    File,
}

/// Represents a node in the directory tree structure
#[derive(Debug)]
pub struct TreeNode {
    /// Name of the file or directory
    name: String,
    /// Type of the node (File or Directory)
    node_type: NodeType,
    /// Child nodes if this is a directory
    children: Vec<TreeNode>,
}

/// Recursively builds the directory tree
fn build_tree(path: &Path) -> Result<TreeNode, MapperError> {
    build_tree_inner(path, true).ok_or_else(|| MapperError::InvalidPath(path.display().to_string()))
}

/// Internal function to recursively build the directory tree
///
/// # Arguments
///
/// * `path` - The path to build the tree from
/// * `is_root` - Whether this is the root node of the tree
///
/// # Returns
///
/// Returns an Option<TreeNode> - None if the path should be filtered out
fn build_tree_inner(path: &Path, is_root: bool) -> Option<TreeNode> {
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| ".".to_string());

    if path.is_dir() {
        // Filter out unwanted directories, but not at the root
        if !is_root && (name == "target" || name == "gen" || name.starts_with('.')) {
            return None;
        }

        // Read directory entries
        let mut children = Vec::new();
        match fs::read_dir(path) {
            Ok(entries) => {
                for entry in entries.flatten() {
                    let child_path = entry.path();
                    if let Some(child) = build_tree_inner(&child_path, false) {
                        children.push(child);
                    }
                }
            }
            Err(e) => {
                eprintln!(
                    "Warning: Failed to read directory '{}': {}",
                    path.display(),
                    e
                );
            }
        }

        // Sort children alphabetically with directories first
        children.sort_by(|a, b| match (&a.node_type, &b.node_type) {
            (NodeType::Directory, NodeType::File) => std::cmp::Ordering::Less,
            (NodeType::File, NodeType::Directory) => std::cmp::Ordering::Greater,
            _ => a.name.cmp(&b.name),
        });

        Some(TreeNode {
            name,
            node_type: NodeType::Directory,
            children,
        })
    } else {
        Some(TreeNode {
            name,
            node_type: NodeType::File,
            children: vec![],
        })
    }
}

/// Holds layout information for a node
struct LayoutNode<'a> {
    node: &'a TreeNode,
    x: i32,
    y: i32,
    width: i32,
    height: i32,
    children: Vec<LayoutNode<'a>>,
}

/// Compute width and height for each node and position children to avoid overlap
fn layout_tree(
    node: &TreeNode,
    x: i32,
    y: i32,
    h_spacing: i32,
    v_spacing: i32,
    char_width: i32,
    padding: i32,
    min_width: i32,
    height: i32,
) -> LayoutNode<'_> {
    let text_len = node.name.chars().count() as i32;
    let width = (text_len * char_width + 2 * padding).max(min_width);
    let mut curr_y = y;
    let mut children = Vec::new();
    let mut subtree_height = 0;
    for child in &node.children {
        let child_layout = layout_tree(
            child,
            x + width + h_spacing,
            curr_y,
            h_spacing,
            v_spacing,
            char_width,
            padding,
            min_width,
            height,
        );
        curr_y += child_layout.height + v_spacing;
        subtree_height += child_layout.height + v_spacing;
        children.push(child_layout);
    }
    if subtree_height > 0 {
        subtree_height -= v_spacing; // Remove extra spacing after last child
    }
    let node_height = height.max(subtree_height);
    LayoutNode {
        node,
        x,
        y: if subtree_height > height {
            y + (subtree_height - height) / 2
        } else {
            y
        },
        width,
        height: node_height,
        children,
    }
}

/// Recursively render SVG for the layout tree
fn svg_for_layout(layout: &LayoutNode, svg: &mut String, id_prefix: &str) {
    let node_id = format!("{}-{}-{}", id_prefix, layout.x, layout.y);
    let (node_color, glow_color) = match layout.node.node_type {
        NodeType::Directory => ("#00fff7", "#00fff7"), // Neon cyan
        NodeType::File => ("#39ff14", "#39ff14"),      // Neon green
    };
    svg.push_str(&format!(
        "<g id='{id}' onmouseover=\"this.querySelector('rect').style.fill='#333'\" onmouseout=\"this.querySelector('rect').style.fill='{color}'\" class='node'><rect x='{x}' y='{y}' width='{w}' height='32' rx='12' fill='{color}' filter='url(#glow)' opacity='0.92'/><text x='{tx}' y='{ty}' font-size='16' fill='#000' filter='url(#textglow)' style='font-family:monospace;letter-spacing:0.5px'>{label}</text>",
        id = node_id,
        x = layout.x,
        y = layout.y,
        w = layout.width,
        color = node_color,
        tx = layout.x + 14,
        ty = layout.y + 22,
        label = layout.node.name
    ));
    if let NodeType::File = layout.node.node_type {
        svg.push_str(&format!("<title>File: {}</title>", layout.node.name));
    }
    svg.push_str("</g>");
    // Draw connectors
    for child in &layout.children {
        let x1 = layout.x + layout.width;
        let y1 = layout.y + 16;
        let x2 = child.x;
        let y2 = child.y + 16;
        let curve = format!(
            "<path d='M{x1},{y1} C{x1plus},{y1} {x2minus},{y2} {x2},{y2}' stroke='{color}' stroke-width='3.5' fill='none' filter='url(#glow)' opacity='0.88' />",
            x1 = x1,
            y1 = y1,
            x1plus = x1 + 30,
            x2minus = x2 - 30,
            x2 = x2,
            y2 = y2,
            color = glow_color
        );
        svg.push_str(&curve);
        svg_for_layout(child, svg, &node_id);
    }
}

/// Generates the interactive SVG map
fn layout_bbox(layout: &LayoutNode, max: &mut (i32, i32)) {
    // max = (max_x, max_y)
    let right = layout.x + layout.width;
    let bottom = layout.y + 32; // Only add node height, not subtree height
    if right > max.0 {
        max.0 = right;
    }
    if bottom > max.1 {
        max.1 = bottom;
    }
    for child in &layout.children {
        layout_bbox(child, max);
    }
}

/// Generates the SVG content with the given layout and dimensions
fn generate_svg_content(layout: &LayoutNode, svg_width: i32, svg_height: i32) -> String {
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' style='background:#14151a' font-family='monospace'>"
    );

    // Add SVG definitions for filters and base styles
    svg.push_str(include_str!("svg_defs.svg"));

    // Add background
    svg.push_str("<rect width='100%' height='100%' fill='#14151a'/>");

    // Generate the tree layout
    svg_for_layout(layout, &mut svg, "root");

    // Add interactive JavaScript
    svg.push_str(include_str!("svg_script.js"));
    svg.push_str("</svg>");

    svg
}

/// Generates an SVG map of the directory structure
///
/// # Arguments
///
/// * `root_path` - The root path to start mapping from
///
/// # Returns
///
/// Returns a Result containing either the SVG string or a MapperError
pub fn generate_svg_map(root_path: &str) -> Result<String, MapperError> {
    let tree = build_tree(Path::new(root_path))?;

    let h_spacing = 40;
    let v_spacing = 20;
    let char_width = 10;
    let padding = 18;
    let min_width = 80;
    let height = 32;

    let layout = layout_tree(
        &tree, 32, 32, h_spacing, v_spacing, char_width, padding, min_width, height,
    );

    let mut max = (0, 0);
    layout_bbox(&layout, &mut max);
    let svg_width = max.0 + 32;
    let svg_height = max.1 + 32;

    Ok(generate_svg_content(&layout, svg_width, svg_height))
}

/// Saves the SVG map to a file at the specified path
///
/// # Arguments
///
/// * `svg` - The SVG content to save
/// * `output_path` - The path where to save the SVG file
///
/// # Returns
///
/// Returns a Result indicating success or failure
pub fn save_svg_map(svg: &str, output_path: &str) -> Result<(), MapperError> {
    fs::write(output_path, svg).map_err(MapperError::IoError)
}

mod drawio_compress;
mod drawio_launcher;
mod drawio_layout;
mod drawio_xml;

fn main() -> Result<(), MapperError> {
    let root_path = ".";
    let tree = build_tree(std::path::Path::new(root_path))?;
    // Generate and save SVG
    let svg = generate_svg_map(root_path)?;
    save_svg_map(&svg, "repo_map.svg")?;
    println!("SVG generated: repo_map.svg");
    // Generate and save draw.io XML
    let file_xml = drawio_xml::generate_drawio_file_xml(&tree);
    std::fs::write("repo_map.drawio", &file_xml)?;
    println!("Draw.io XML generated: repo_map.drawio");
    let model_xml = drawio_xml::generate_mxgraphmodel_xml(&tree);
    // Compress, encode, and launch draw.io
    match drawio_compress::compress_and_encode(&model_xml) {
        Ok(encoded) => match drawio_launcher::launch_drawio_with_xml(&encoded) {
            Ok(()) => println!("Opened draw.io in browser."),
            Err(e) => eprintln!("Failed to launch draw.io: {e}"),
        },
        Err(e) => eprintln!("Compression/encoding failed: {e}"),
    }
    Ok(())
}
