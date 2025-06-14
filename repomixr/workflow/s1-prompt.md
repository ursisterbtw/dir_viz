# Prompt: Comprehensive Analysis and Visualization of repomix XML Output

---

You will be provided with a `.xml` file generated by **repomix**, representing the structure, metadata, and elements of a codebase. Your task is to perform an in-depth analysis of the file and generate a structured, Markdown-formatted report including the following diagrams and insights:

## 📦 1. High-Level Project Architecture Diagram

- Visually represent the system’s macro-level organization (layers, domains, components, services).
- Group related components logically and label them clearly to show responsibilities.
- Highlight major architectural boundaries, e.g., frontend/backend, API layers, data pipelines, etc.
- Use **Mermaid** syntax for diagram creation and include explanatory notes for non-obvious relationships.

## 🗂 2. Project Structure Hierarchy

- Render a **directory tree or package/module hierarchy** that reflects the codebase’s physical and logical layout.
- Indicate key folders and what type of content they contain (e.g., services, configs, utilities).
- Use collapsible or nested formatting (via Markdown or Mermaid) to aid readability.

## 🔄 3. Data Flow & Sequence Diagrams

- Construct **data flow diagrams** that track how information moves between major components.
- Create **sequence diagrams** for core workflows (e.g., authentication, data fetch/store, user actions).
- Emphasize runtime interactions and message passing across services or modules.
- Where applicable, annotate with timing/order information and role responsibilities.

## 🔗 4. Dependency Graph

- Generate a **dependency graph** illustrating internal and external module relationships.
- Highlight critical dependencies, including third-party libraries, services, or packages.
- Flag any problematic patterns such as **circular dependencies**, tight couplings, or bloated modules.
- Offer commentary on the modularity and extensibility of the system based on the graph.

## 🧬 5. UML Class Diagrams

- Identify and diagram **key classes, interfaces, and abstract types**.
- Illustrate relationships such as inheritance, composition, aggregation, and interface implementation.
- Include class attributes and methods where discernible from metadata.
- Add functional summaries for each major class/component and describe their responsibilities.

## 🧠 6. Design Patterns & Implementation Strategies

- Detect and describe **design patterns** (e.g., Singleton, Factory, MVC, Observer) used in the architecture.
- Map the flow of control and data during representative use cases or execution paths.
- Comment on **code quality**, separation of concerns, and adherence to best practices.

---

## ✅ Additional Analysis Guidelines

- All diagrams must use **Mermaid syntax** where applicable and be **well-labeled and logically grouped**.
- Structure the Markdown report with clear **headings, subheadings, code blocks**, and a **Table of Contents**.
- Provide **brief explanations** for each diagram and visual artifact.
- List any **assumptions** you make when relationships or component roles are inferred.
- Surface potential areas of technical debt, including:
  - Placeholder functions, TODO comments, or partial implementations
  - Performance bottlenecks or optimization opportunities
  - Security gaps or configuration red flags
  - Inconsistencies in documentation, naming, or architecture

The final output should help both technical and non-technical stakeholders understand the system at multiple levels: structural, behavioral, and strategic.
