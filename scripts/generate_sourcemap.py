import json
import os
import base64

def generate_sourcemap():
    js_file_path = 'js/webflow-script.js'
    
    # Read the original JS file
    with open(js_file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Create a basic source map
    # This maps the minified file positions to original positions
    # For vanilla JS, we'll create a simple 1:1 mapping
    lines = js_content.split('\n')
    mappings = []
    
    # Generate basic mappings (1:1 mapping for each line)
    for line_num in range(len(lines)):
        # Basic VLQ encoding for the mapping
        # Format: generated line, generated column, source index, original line, original column
        mappings.append('AACA')  # Simple 1:1 mapping
    
    map_content = {
        'version': 3,
        'file': 'webflow-script.js',
        'sourceRoot': '',
        'sources': ['webflow-script.js'],
        'names': [],
        'mappings': ';'.join(mappings),
        'sourcesContent': [js_content]
    }

    # Write source map file
    map_file_path = js_file_path + '.map'
    with open(map_file_path, 'w', encoding='utf-8') as f:
        json.dump(map_content, f)

    # Add sourceMappingURL comment to JS file if not already present
    if '//# sourceMappingURL=' not in js_content:
        with open(js_file_path, 'a', encoding='utf-8') as f:
            f.write('\n//# sourceMappingURL=webflow-script.js.map')

    print(f"Source map generated at {map_file_path}")

if __name__ == '__main__':
    generate_sourcemap()
