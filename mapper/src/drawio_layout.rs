use crate::TreeNode;
use std::collections::HashMap;

/// Stores the computed position for each node by id
pub struct NodeLayout<'a> {
    pub positions: HashMap<u32, (i32, i32)>,    // id -> (x, y)
    pub id_to_node: HashMap<u32, &'a TreeNode>, // id -> node
    pub next_id: u32,
}

impl NodeLayout<'_> {
    pub fn new() -> Self {
        NodeLayout {
            positions: HashMap::new(),
            id_to_node: HashMap::new(),
            next_id: 2,
        }
    }
}

/// Recursively assign (x, y) positions for a tree, returning the node id.
pub fn layout_tree<'a>(
    node: &'a TreeNode,
    depth: i32,
    y_offset: &mut i32,
    layout: &mut NodeLayout<'a>,
    parent_id: u32,
    edges: &mut Vec<(u32, u32)>,
) -> u32 {
    let local_y = *y_offset;
    let id = layout.next_id;
    layout.next_id += 1;
    layout.id_to_node.insert(id, node);

    // Assign position: landscape (x = depth, y = sibling order)
    layout.positions.insert(id, (depth * 240, local_y));

    // Lay out children
    let mut child_y = local_y;
    for child in &node.children {
        let child_id = layout_tree(child, depth + 1, &mut child_y, layout, id, edges);
        edges.push((id, child_id));
        child_y += 90;
    }
    id
}
