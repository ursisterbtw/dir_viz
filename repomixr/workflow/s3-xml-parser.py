import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_repomix_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    structure = {
        "project": {
            "name": root.attrib.get("name", "UnnamedProject"),
            "structure": {},
            "classes": [],
            "functions": [],
            "dependencies": [],
            "todos": [],
        }
    }

    for elem in root.iter():
        tag = elem.tag.lower()
        attrib = elem.attrib

        if tag == "file":
            path = attrib.get("path")
            structure["project"]["structure"].setdefault(path, {"type": "file"})

        elif tag == "directory":
            path = attrib.get("path")
            structure["project"]["structure"].setdefault(path, {"type": "directory"})

        elif tag == "class":
            cls = {
                "name": attrib.get("name"),
                "file": attrib.get("file"),
                "inherits": (
                    attrib.get("inherits", "").split(",")
                    if "inherits" in attrib
                    else []
                ),
                "methods": [],
            }
            structure["project"]["classes"].append(cls)

        elif tag == "function":
            fn = {
                "name": attrib.get("name"),
                "file": attrib.get("file"),
                "defined_in": attrib.get("class", None),
            }
            structure["project"]["functions"].append(fn)

        elif tag in ("todo", "fixme"):
            structure["project"]["todos"].append(
                {
                    "file": attrib.get("file"),
                    "line": attrib.get("line"),
                    "comment": elem.text.strip() if elem.text else "",
                }
            )

        elif tag == "dependency":
            structure["project"]["dependencies"].append(
                {
                    "source": attrib.get("from"),
                    "target": attrib.get("to"),
                    "type": attrib.get("type", "import"),
                }
            )

    return structure


def write_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_markdown_summary(data, path):
    project = data["project"]
    lines = [
        f"# Project Summary: {project['name']}\n",
        "## Table of Contents",
        "- [Structure](#structure)",
        "- [Classes](#classes)",
        "- [Functions](#functions)",
        "- [Dependencies](#dependencies)",
        "- [TODOs and FIXMEs](#todos-and-fixmes)\n",
        "## Structure",
    ]
    lines.extend(
        f"- `{path_key}` ({meta['type']})"
        for path_key, meta in sorted(project["structure"].items())
    )
    lines.append("\n## Classes")
    for cls in project["classes"]:
        inherits = ", ".join(cls["inherits"]) if cls["inherits"] else "None"
        lines.append(f"- **{cls['name']}** in `{cls['file']}` inherits: {inherits}")

    lines.append("\n## Functions")
    for fn in project["functions"]:
        owner = f"(in class {fn['defined_in']})" if fn["defined_in"] else ""
        lines.append(f"- `{fn['name']}` in `{fn['file']}` {owner}")

    lines.append("\n## Dependencies")
    lines.extend(
        f"- `{dep['source']}` ➜ `{dep['target']}` ({dep['type']})"
        for dep in project["dependencies"]
    )
    lines.append("\n## TODOs and FIXMEs")
    lines.extend(
        f"- `{todo['file']}`:{todo['line']} → {todo['comment']}"
        for todo in project["todos"]
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def normalize_id(path):
    return path.strip("/").replace("/", "_").replace(".", "_")


def write_mermaid_dependency_graph(data, path):
    lines = ["```mermaid", "graph TD"]
    lines.extend(
        f"{normalize_id(dep['source'])} --> {normalize_id(dep['target'])}"
        for dep in data["project"]["dependencies"]
    )
    lines.append("```")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_mermaid_class_diagram(data, path):
    lines = ["```mermaid", "classDiagram"]
    for cls in data["project"]["classes"]:
        lines.append(f"class {cls['name']}")
        lines.extend(f"{base} <|-- {cls['name']}" for base in cls["inherits"] if base)
    lines.append("```")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_mermaid_directory_tree(data, path):
    lines = ["```mermaid", "graph TD"]
    structure = data["project"]["structure"]
    for item_path, meta in structure.items():
        if parent := "/".join(item_path.strip("/").split("/")[:-1]):
            lines.append(f"{normalize_id(parent)} --> {normalize_id(item_path)}")
        icon = "📁" if meta["type"] == "directory" else "📄"
        label = item_path.split("/")[-1]
        lines.append(f'{normalize_id(item_path)}["{icon} {label}"]')
    lines.append("```")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def update_planning_and_tasks(data, output_dir):
    planning_path = output_dir / "PLANNING.md"
    tasks_path = output_dir / "TASKS.md"

    todos = data["project"]["todos"]
    deps = data["project"]["dependencies"]

    planning = [
        "# PLANNING.md",
        "## Architecture and Quality Objectives",
        "- Visualize core components and relationships.",
        "- Resolve incomplete implementations and todos.",
        "- Refactor for modularity and testability.",
        "- Identify performance-critical or tightly coupled code.\n",
        "## Technical Concerns",
    ]

    if todos:
        planning.append("- [ ] Address TODOs/FIXMEs in source files.")
    if any("circular" in d.get("type", "").lower() for d in deps):
        planning.append("- [ ] Investigate potential circular dependencies.")
    planning += [
        "- [ ] Review class hierarchies for overengineering or tight coupling.",
        "- [ ] Evaluate unused or overly large modules.\n",
        "## Completed Diagrams",
        "- [x] Directory Tree",
        "- [x] Class Diagram",
        "- [x] Dependency Graph",
    ]

    with open(planning_path, "w", encoding="utf-8") as f:
        f.write("\n".join(planning))

    tasks = ["# TASKS.md", "## Parsed TODOs"]
    for todo in todos:
        file = todo["file"]
        comment = todo["comment"].lower()
        priority = (
            "High"
            if any(w in comment for w in ["fix", "security"])
            else (
                "Medium"
                if any(w in comment for w in ["optimize", "refactor"])
                else "Low"
            )
        )
        tasks.append(f"- [{priority}] `{file}`:{todo['line']} – {todo['comment']}")

    tasks.append("\n## Output Verification")
    tasks += [
        "- [x] JSON structure saved",
        "- [x] Markdown summary written",
        "- [x] Mermaid diagrams generated",
    ]

    with open(tasks_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tasks))


def main():
    parser = argparse.ArgumentParser(
        description="Analyze repomix .xml output and generate diagrams + documentation."
    )
    parser.add_argument(
        "xml_path", type=str, help="Path to the repomix output .xml file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="repomix_report",
        help="Output directory for reports",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    data = parse_repomix_xml(args.xml_path)
    write_json(data, output_dir / "repomix_output.json")
    write_markdown_summary(data, output_dir / "repomix_summary.md")
    write_mermaid_dependency_graph(data, output_dir / "repomix_dependencies.mmd")
    write_mermaid_class_diagram(data, output_dir / "repomix_classes.mmd")
    write_mermaid_directory_tree(data, output_dir / "repomix_structure.mmd")
    update_planning_and_tasks(data, output_dir)
    print(f"✅ Analysis complete. Output saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
