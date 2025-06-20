use crate::TreeNode;
use crate::drawio_layout;

pub fn generate_mxgraphmodel_xml(root: &TreeNode) -> String {
    let mut xml = String::new();
    // Set background to black
    xml.push_str("<mxGraphModel background=\"#000000\"><root>\n");
    xml.push('\n');
    // Add the root cell (draw.io requires id="0" and id="1" for the graph base)
    xml.push_str("<mxCell id=\"0\" />\n<mxCell id=\"1\" parent=\"0\" />\n");
    let mut layout = drawio_layout::NodeLayout::new();
    let mut x_offset = 0;
    let mut edges = Vec::new();
    let _root_id = drawio_layout::layout_tree(root, 0, &mut x_offset, &mut layout, 1, &mut edges);

    // Calculate bounding box for all node positions
    let (min_x, max_x, min_y, max_y) = layout
        .positions
        .values()
        .fold((i32::MAX, i32::MIN, i32::MAX, i32::MIN), |acc, &(x, y)| {
            (acc.0.min(x), acc.1.max(x), acc.2.min(y), acc.3.max(y))
        });
    let bbox_height = max_y - min_y;
    // Start x at 0, center y
    let offset_x = -min_x;
    let offset_y = -min_y - bbox_height / 2;

    // Emit each node exactly once using the id_to_node mapping, shifted for landscape
    for (&id, node) in &layout.id_to_node {
        let (x, y) = layout.positions[&id];
        // Dynamic width: 12px per char + 32px padding (min 80)
        let label_len = node.name.chars().count() as i32;
        let width = (label_len * 12 + 32).max(80);
        let style = match node.node_type {
            crate::NodeType::Directory => {
                "rounded=1;arcSize=30;fillColor=#00fff7;strokeColor=#00fff7;strokeWidth=3.5;opacity=92;fontColor=#000;fontSize=16;fontFamily=monospace;shadow=1;glow=1;glowColor=#00fff7;"
            }
            crate::NodeType::File => {
                "rounded=1;arcSize=30;fillColor=#39ff14;strokeColor=#39ff14;strokeWidth=3.5;opacity=92;fontColor=#000;fontSize=16;fontFamily=monospace;shadow=1;glow=1;glowColor=#39ff14;"
            }
        };
        let value = &node.name;
        xml.push_str(&format!(
            "<mxCell id=\"{}\" value=\"{}\" style=\"{}\" parent=\"1\" vertex=\"1\"><mxGeometry x=\"{}\" y=\"{}\" width=\"{}\" height=\"32\" as=\"geometry\"/></mxCell>\n",
            id, value, style, x + offset_x, y + offset_y, width
        ));
    }

    // Add all edges after nodes
    for (parent, child) in edges {
        xml.push_str(&format!(
            "<mxCell id=\"e{parent}_{child}\" edge=\"1\" parent=\"1\" source=\"{parent}\" target=\"{child}\" style=\"endArrow=none;strokeColor=#00fff7;strokeWidth=3.5;opacity=88;curved=1;shadow=1;glow=1;glowColor=#00fff7;\"><mxGeometry relative=\"1\" as=\"geometry\"/></mxCell>\n"
        ));
    }
    xml.push_str("</root></mxGraphModel>");
    xml
}

/// Generates a full draw.io file XML for saving to disk.
pub fn generate_drawio_file_xml(root: &TreeNode) -> String {
    let model = generate_mxgraphmodel_xml(root);
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<mxfile host=\"app.diagrams.net\">\n  <diagram name=\"Project Map\">{model}</diagram>\n</mxfile>"
    )
}

fn add_node_xml_with_edges(
    node: &TreeNode,
    parent_id: u32,
    id: &mut u32,
    xml: &mut String,
    edges: &mut Vec<(u32, u32)>,
) {
    let this_id = *id;
    *id += 1;
    // For simplicity, use rectangles for all nodes
    let style = match node.node_type {
        crate::NodeType::Directory => {
            "rounded=1;fillColor=#00fff7;strokeColor=#00fff7;opacity=92;fontColor=#000000;fontStyle=1;"
        }
        crate::NodeType::File => {
            "rounded=1;fillColor=#39ff14;strokeColor=#39ff14;opacity=92;fontColor=#000000;fontStyle=1;"
        }
    };
    xml.push_str(&format!(
        "<mxCell id=\"{}\" value=\"{}\" style=\"{}\" parent=\"{}\" vertex=\"1\"><mxGeometry x=\"{}\" y=\"{}\" width=\"120\" height=\"40\" as=\"geometry\"/></mxCell>\n",
        this_id,
        node.name.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;"),
        style,
        parent_id,
        50 * this_id, // x
        50 * this_id, // y
    ));
    for child in &node.children {
        let child_id = *id;
        // Add edge from this node to child
        edges.push((this_id, child_id));
        add_node_xml_with_edges(child, this_id, id, xml, edges);
    }
}
