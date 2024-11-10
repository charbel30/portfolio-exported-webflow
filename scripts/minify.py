import os
import subprocess
import glob
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_node_modules():
    """Ensure required node packages are installed locally"""
    packages = [
        'terser',          # JS minification
        'clean-css-cli',   # CSS minification
        'html-minifier'    # HTML minification
    ]
    
    if not os.path.exists('node_modules'):
        try:
            logger.info("Installing required node packages...")
            subprocess.run(['npm', 'init', '-y'], check=True, capture_output=True)
            subprocess.run(['npm', 'install', '--save-dev'] + packages, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install node packages: {e}")
            raise

def ensure_dist_directory():
    """Ensure dist directory exists and is empty"""
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')

def create_output_directory(file_path):
    """Create output directory structure in dist"""
    output_dir = os.path.join('dist', os.path.dirname(file_path))
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join('dist', file_path)

def minify_javascript(file_path):
    """Minify a JavaScript file using terser"""
    try:
        output_path = create_output_directory(file_path)
        logger.info(f"Minifying JavaScript: {file_path}")
        
        # Use local terser from node_modules
        subprocess.run([
            'node_modules/.bin/terser',
            file_path,
            '--compress',
            '--mangle',
            '--output', output_path
        ], check=True, capture_output=True)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to minify {file_path}: {e}")
        raise

def minify_css(file_path):
    """Minify a CSS file using clean-css"""
    try:
        output_path = create_output_directory(file_path)
        logger.info(f"Minifying CSS: {file_path}")
        
        # Use local cleancss from node_modules
        subprocess.run([
            'node_modules/.bin/cleancss',
            '-o', output_path,
            file_path
        ], check=True, capture_output=True)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to minify {file_path}: {e}")
        raise

def minify_html(file_path):
    """Minify an HTML file using html-minifier"""
    try:
        output_path = create_output_directory(file_path)
        logger.info(f"Minifying HTML: {file_path}")
        
        # Use local html-minifier from node_modules
        subprocess.run([
            'node_modules/.bin/html-minifier',
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
        ], check=True, capture_output=True)
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to minify {file_path}: {e}")
        raise

def copy_minified_files():
    """Copy minified files from dist back to original locations"""
    try:
        for root, _, files in os.walk('dist'):
            for file in files:
                dist_path = os.path.join(root, file)
                original_path = dist_path.replace('dist/', '', 1)
                shutil.copy2(dist_path, original_path)
    except Exception as e:
        logger.error(f"Failed to copy minified files: {e}")
        raise

def main():
    try:
        # Ensure required packages are installed
        ensure_node_modules()
        
        # Prepare dist directory
        ensure_dist_directory()
        
        # Get all files to minify, excluding node_modules and dist
        js_files = [f for f in glob.glob('**/*.js', recursive=True)
                   if 'node_modules' not in f and 'dist' not in f]
        css_files = [f for f in glob.glob('**/*.css', recursive=True)
                    if 'node_modules' not in f and 'dist' not in f]
        html_files = [f for f in glob.glob('**/*.html', recursive=True)
                     if 'node_modules' not in f and 'dist' not in f]
        
        # Process JavaScript files
        for js_file in js_files:
            minify_javascript(js_file)
        
        # Process CSS files
        for css_file in css_files:
            minify_css(css_file)
        
        # Process HTML files
        for html_file in html_files:
            minify_html(html_file)
        
        # Copy minified files back to original locations
        copy_minified_files()
        
        # Cleanup dist directory
        shutil.rmtree('dist')
        
        logger.info("Minification completed successfully!")
        
    except Exception as e:
        logger.error(f"Minification failed: {e}")
        # Cleanup on failure
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        raise

if __name__ == "__main__":
    main()
