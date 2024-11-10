import os
import re
import json
import cssmin
import jsmin
import htmlmin
from bs4 import BeautifulSoup
from pathlib import Path
import shutil
from PIL import Image
import requests
from urllib.parse import urljoin
import hashlib

class PerformanceOptimizer:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir)
        self.dist_dir = self.root_dir / 'dist'
        self.critical_css = set()
        self.critical_js = set()
        
    def setup_dist_directory(self):
        """Create clean dist directory"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(parents=True)
        
        # Create necessary subdirectories
        (self.dist_dir / 'css').mkdir()
        (self.dist_dir / 'js').mkdir()
        (self.dist_dir / 'images').mkdir()

    def extract_critical_css(self, html_file):
        """Extract critical CSS rules needed for above-the-fold content"""
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find elements visible in the viewport
            viewport_elements = soup.find_all(lambda tag: not tag.get('style', '').find('display: none') >= 0)
            
            for element in viewport_elements:
                if element.get('class'):
                    self.critical_css.update(element['class'])

    def optimize_css(self, css_file):
        """Optimize CSS by inlining critical CSS and deferring non-critical"""
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split into rules
        rules = re.findall(r'([^}]+})', content)
        critical_rules = []
        non_critical_rules = []
        
        for rule in rules:
            is_critical = False
            for class_name in self.critical_css:
                if f'.{class_name}' in rule:
                    is_critical = True
                    break
            
            if is_critical:
                critical_rules.append(rule)
            else:
                non_critical_rules.append(rule)
        
        # Minify both parts
        critical_css = cssmin.cssmin(''.join(critical_rules))
        non_critical_css = cssmin.cssmin(''.join(non_critical_rules))
        
        return critical_css, non_critical_css

    def optimize_js(self, js_file):
        """Split JavaScript into critical and non-critical chunks"""
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple heuristic: functions used in onload/DOMContentLoaded are critical
        critical_pattern = r'(document\.addEventListener\([\'"]DOMContentLoaded[\'"]|window\.onload\s*=)'
        if re.search(critical_pattern, content):
            # Extract the event listener and its content as critical
            critical_js = jsmin.jsmin(content)
            non_critical_js = ''
        else:
            # Consider it non-critical
            critical_js = ''
            non_critical_js = jsmin.jsmin(content)
        
        return critical_js, non_critical_js

    def optimize_images(self, image_path):
        """Optimize images for web delivery"""
        try:
            img = Image.open(image_path)
            
            # Calculate target size (maintain aspect ratio)
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Optimize based on format
            output_path = self.dist_dir / 'images' / image_path.name
            if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                img.save(output_path, 'JPEG', quality=85, optimize=True)
            elif image_path.suffix.lower() == '.png':
                img.save(output_path, 'PNG', optimize=True)
            elif image_path.suffix.lower() == '.webp':
                img.save(output_path, 'WEBP', quality=85)
                
            return output_path
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")
            return image_path

    def add_cache_headers(self, file_path):
        """Generate cache control headers for static assets"""
        # Generate ETag based on file content
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        headers = {
            'Cache-Control': 'public, max-age=31536000, immutable',
            'ETag': f'"{file_hash}"'
        }
        
        return headers

    def optimize_html(self, html_file, critical_css, critical_js):
        """Optimize HTML with inline critical resources and deferred loading"""
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Add critical CSS inline
        if critical_css:
            style_tag = soup.new_tag('style')
            style_tag.string = critical_css
            soup.head.append(style_tag)
        
        # Add critical JS inline
        if critical_js:
            script_tag = soup.new_tag('script')
            script_tag.string = critical_js
            soup.head.append(script_tag)
        
        # Update resource paths and add defer/async
        for css_link in soup.find_all('link', rel='stylesheet'):
            css_link['href'] = css_link['href'].replace('/css/', '/dist/css/')
            # Add media="print" onload hack for non-critical CSS
            css_link['media'] = 'print'
            css_link['onload'] = "this.media='all'"
        
        for script in soup.find_all('script', src=True):
            if script['src'].startswith('/js/'):
                script['src'] = script['src'].replace('/js/', '/dist/js/')
                # Add defer to non-critical scripts
                if 'jquery' not in script['src'].lower():
                    script['defer'] = ''
        
        # Optimize images
        for img in soup.find_all('img'):
            if img.get('src'):
                img['loading'] = 'lazy'  # Add lazy loading
                if not img['src'].startswith('data:'):
                    img['src'] = img['src'].replace('/images/', '/dist/images/')
        
        # Remove unnecessary attributes and comments
        for tag in soup.find_all(True):
            if tag.get('style') == '':
                del tag['style']
            if tag.get('class') and not tag['class']:
                del tag['class']
        
        # Minify HTML
        minified_html = htmlmin.minify(str(soup),
                                     remove_empty_space=True,
                                     remove_comments=True)
        
        # Save optimized file
        output_path = self.dist_dir / html_file.relative_to(self.root_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_html)

    def run_optimization(self):
        """Run the complete optimization process"""
        print("Starting performance optimization...")
        
        # Setup
        self.setup_dist_directory()
        
        # Process HTML files first to identify critical resources
        html_files = list(self.root_dir.rglob('*.html'))
        for html_file in html_files:
            self.extract_critical_css(html_file)
        
        # Optimize CSS files
        css_files = list(self.root_dir.rglob('*.css'))
        css_optimizations = {}
        for css_file in css_files:
            critical, non_critical = self.optimize_css(css_file)
            css_optimizations[css_file] = (critical, non_critical)
            
            # Save non-critical CSS
            if non_critical:
                output_path = self.dist_dir / 'css' / css_file.name
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(non_critical)
                # Add cache headers
                self.add_cache_headers(output_path)
        
        # Optimize JavaScript files
        js_files = list(self.root_dir.rglob('*.js'))
        js_optimizations = {}
        for js_file in js_files:
            critical, non_critical = self.optimize_js(js_file)
            js_optimizations[js_file] = (critical, non_critical)
            
            # Save non-critical JS
            if non_critical:
                output_path = self.dist_dir / 'js' / js_file.name
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(non_critical)
                # Add cache headers
                self.add_cache_headers(output_path)
        
        # Optimize images
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_files.extend(self.root_dir.rglob(f'*{ext}'))
        
        for image_file in image_files:
            optimized_path = self.optimize_images(image_file)
            # Add cache headers
            self.add_cache_headers(optimized_path)
        
        # Finally, optimize HTML files with the critical resources
        for html_file in html_files:
            critical_css = ''
            critical_js = ''
            
            # Collect critical CSS from all stylesheets
            for css_file, (crit_css, _) in css_optimizations.items():
                critical_css += crit_css
            
            # Collect critical JS from all scripts
            for js_file, (crit_js, _) in js_optimizations.items():
                critical_js += crit_js
            
            self.optimize_html(html_file, critical_css, critical_js)
        
        print("\nOptimization complete! Check the 'dist' directory for optimized files.")
        return {
            'html_files_processed': len(html_files),
            'css_files_processed': len(css_files),
            'js_files_processed': len(js_files),
            'images_processed': len(image_files)
        }

if __name__ == '__main__':
    optimizer = PerformanceOptimizer()
    stats = optimizer.run_optimization()
    print("\nOptimization Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
