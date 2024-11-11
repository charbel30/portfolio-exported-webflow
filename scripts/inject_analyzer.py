import os
import re

def inject_analyzer():
    # Read the HTML files
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the webflow-script.js script tag
        webflow_script = re.search(r'<script[^>]*src="[^"]*webflow-script\.js"[^>]*>', content)
        if not webflow_script:
            continue
            
        # Add our analyzer script before webflow-script.js
        analyzer_script = '<script src="js/analyze-webflow.js"></script>'
        modified_content = content.replace(
            webflow_script.group(0),
            analyzer_script + '\n  ' + webflow_script.group(0)
        )
        
        # Write the modified content back
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f'Injected analyzer into {html_file}')

if __name__ == '__main__':
    inject_analyzer()
