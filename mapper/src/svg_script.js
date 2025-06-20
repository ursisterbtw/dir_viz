document.addEventListener('DOMContentLoaded', () => {
    const nodes = document.querySelectorAll('.node');
    nodes.forEach(node => {
        const rect = node.querySelector('rect');
        if (node.querySelector('title')?.textContent?.startsWith('File:')) {
            return; // Skip files, only handle directories
        }

        // Add click handler
        node.addEventListener('click', (e) => {
            e.stopPropagation();
            const children = Array.from(node.children).filter(c => c.tagName === 'g');
            const isExpanded = children[0]?.style.display !== 'none';

            // Toggle children visibility
            children.forEach(c => c.style.display = isExpanded ? 'none' : '');

            // Update appearance
            rect.style.fill = isExpanded ? '#00fff7' : '#0066cc';
        });
    });
});
