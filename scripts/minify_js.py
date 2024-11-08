import os
import subprocess
import glob

def install_terser():
    """Install terser package for JS minification"""
    try:
        subprocess.run(['npm', 'list', '-g', 'terser'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Installing terser...")
        subprocess.run(['npm', 'install', '-g', 'terser'], check=True)

def minify_javascript(file_path):
    """Minify a JavaScript file using terser"""
    try:
        # Create minified filename while preserving original
        output_path = file_path.rsplit('.js', 1)[0] + '.min.js'
        
        # Get original size
        original_size = os.path.getsize(file_path)
        
        # Run terser
        subprocess.run([
            'terser',
            file_path,
            '--compress',
            'pure_funcs=[console.log]',
            '--mangle',
            '--output', output_path
        ], check=True)
        
        # Get minified size
        minified_size = os.path.getsize(output_path)
        
        # Calculate reduction
        reduction = (original_size - minified_size) / original_size * 100
        
        print(f"Successfully minified: {file_path}")
        print(f"Original size: {original_size/1024:.2f}KB")
        print(f"Minified size: {minified_size/1024:.2f}KB")
        print(f"Reduction: {reduction:.1f}%")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error minifying {file_path}: {e}")
        return False

def main():
    # Install terser if needed
    install_terser()
    
    # Find all JS files (excluding node_modules and already minified files)
    js_files = [f for f in glob.glob('**/*.js', recursive=True) 
                if not ('node_modules' in f or f.endswith('.min.js'))]
    
    if not js_files:
        print("No JavaScript files found")
        return
    
    print(f"Found {len(js_files)} JavaScript files to minify")
    
    # Minify each JavaScript file
    for js_file in js_files:
        print(f"\nProcessing: {js_file}")
        minify_javascript(js_file)

if __name__ == "__main__":
    main()