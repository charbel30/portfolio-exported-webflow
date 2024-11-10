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
        'terser@5.24.0',    # JS minification - pinned version
        'clean-css-cli',     # CSS minification
        'html-minifier'      # HTML minification
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
        # Skip already minified files
        if file_path.endswith('.min.js'):
            logger.info(f"Skipping already minified file: {file_path}")
            output_path = create_output_directory(file_path)
            shutil.copy2(file_path, output_path)
            return output_path

        output_path = create_output_directory(file_path)
        logger.info(f"Minifying JavaScript: {file_path}")
        
        # Base terser options
        terser_cmd = [
            'node_modules/.bin/terser',
            file_path,
            '--compress',
            'defaults=false,unused=false,dead_code=false',  # Less aggressive compression
            '--mangle', 'reserved=["$"]',  # Preserve jQuery's $ variable
            '--output', output_path
        ]
        
        # Add specific options for legacy/modern files
        if '.legacy.js' in file_path:
            terser_cmd.extend(['--ecma', '5'])
        elif '.modern.js' in file_path:
            terser_cmd.extend(['--ecma', '2015'])
        
        # Run terser with output capture
        result = subprocess.run(
            terser_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to minify {file_path}")
        logger.error(f"Terser stderr: {e.stderr}")
        # Copy original file as fallback
        logger.info(f"Using original file as fallback for: {file_path}")
        output_path = create_output_directory(file_path)
        shutil.copy2(file_path, output_path)
        return output_path

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
        # Copy original file as fallback
        logger.info(f"Using original file as fallback for: {file_path}")
        output_path = create_output_directory(file_path)
        shutil.copy2(file_path, output_path)
        return output_path

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
        # Copy original file as fallback
        logger.info(f"Using original file as fallback for: {file_path}")
        output_path = create_output_directory(file_path)
        shutil.copy2(file_path, output_path)
        return output_path

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
            try:
                minify_javascript(js_file)
            except Exception as e:
                logger.error(f"Error processing {js_file}: {e}")
                continue
        
        # Process CSS files
        for css_file in css_files:
            try:
                minify_css(css_file)
            except Exception as e:
                logger.error(f"Error processing {css_file}: {e}")
                continue
        
        # Process HTML files
        for html_file in html_files:
            try:
                minify_html(html_file)
            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
                continue
        
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
