
import os
import subprocess
import glob

def install_node_packages():
    """Install required node packages for minification"""
    packages = [
        'terser',          # JS minification
        'clean-css-cli',   # CSS minification
        'html-minifier'    # HTML minification
    ]
    
    subprocess.run(['npm', 'install', '-g'] + packages, check=True)

def minify_javascript(file_path):
    """Minify a JavaScript file using terser"""
    output_path = file_path.replace('.js', '.min.js')
    subprocess.run([
        'terser',
        file_path,
        '--compress',
        '--mangle',
        '--output', output_path
    ], check=True)
    os.replace(output_path, file_path)

def minify_css(file_path):
    """Minify a CSS file using clean-css"""
    output_path = file_path.replace('.css', '.min.css')
    subprocess.run([
        'cleancss',
        '-o', output_path,
        file_path
    ], check=True)
    os.replace(output_path, file_path)

def minify_html(file_path):
    """Minify an HTML file using html-minifier"""
    output_path = file_path.replace('.html', '.min.html')
    subprocess.run([
        'html-minifier',
        '--collapse-whitespace',
        '--remove-comments',
        '--remove-optional-tags',
        '--remove-redundant-attributes',
        '--remove-script-type-attributes',
        '--remove-tag-whitespace',
        '--use-short-doctype',
        '--minify-css', 'true',
        '--minify-js', 'true',
        '-o', output_path,
        file_path
    ], check=True)
    os.replace(output_path, file_path)

def main():
    # Install required packages
    install_node_packages()
    
    # Get all files to minify
    js_files = glob.glob('**/*.js', recursive=True)
    css_files = glob.glob('**/*.css', recursive=True)
    html_files = glob.glob('**/*.html', recursive=True)
    
    # Minify JavaScript files
    for js_file in js_files:
        print(f"Minifying {js_file}")
        minify_javascript(js_file)
    
    # Minify CSS files
    for css_file in css_files:
        print(f"Minifying {css_file}")
        minify_css(css_file)
    
    # Minify HTML files
    for html_file in html_files:
        print(f"Minifying {html_file}")
        minify_html(html_file)

if __name__ == "__main__":
    main()