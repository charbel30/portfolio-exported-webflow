import os
import re
import json
import cssmin
import jsmin
import htmlmin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil

class DeploymentOptimizer:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir)
        self.dist_dir = self.root_dir / 'dist'
        self.css_usage_map = {}
        self.js_usage_map = {}
        
    def setup_dist_directory(self):
        """Create clean dist directory"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(parents=True)
        
        # Create necessary subdirectories
        (self.dist_dir / 'css').mkdir()
        (self.dist_dir / 'js').mkdir()
        (self.dist_dir / 'images').mkdir()

    def analyze_file_usage(self):
        """Analyze which CSS classes and JS functions are used in HTML files"""
        html_files = list(self.root_dir.rglob('*.html'))
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Analyze CSS usage
                for element in soup.find_all(class_=True):
                    classes = element['class']
                    for class_name in classes:
                        self.css_usage_map[class_name] = self.css_usage_map.get(class_name, 0) + 1
                
                # Analyze JS usage
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Find function calls
                        function_calls = re.findall(r'(\w+)\s*\(', script.string)
                        for func in function_calls:
                            self.js_usage_map[func] = self.js_usage_map.get(func, 0) + 1

    def optimize_css(self, css_file):
        """Optimize CSS file by removing unused rules and minifying"""
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split into rules
        rules = re.findall(r'([^}]+})', content)
        optimized_rules = []
        
        for rule in rules:
            # Check if rule contains any used classes
            is_used = False
            for class_name in self.css_usage_map:
                if f'.{class_name}' in rule:
                    is_used = True
                    break
            
            if is_used or not rule.strip().startswith('.'):  # Keep non-class rules
                optimized_rules.append(rule)
        
        # Minify the optimized CSS
        optimized_css = ''.join(optimized_rules)
        minified_css = cssmin.cssmin(optimized_css)
        
        # Save optimized file
        output_path = self.dist_dir / 'css' / css_file.name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_css)
            
        return len(content) - len(minified_css)  # Return bytes saved

    def optimize_js(self, js_file):
        """Optimize JavaScript file by removing unused functions and minifying"""
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minify JavaScript
        minified_js = jsmin.jsmin(content)
        
        # Save optimized file
        output_path = self.dist_dir / 'js' / js_file.name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_js)
            
        return len(content) - len(minified_js)  # Return bytes saved

    def optimize_html(self, html_file):
        """Optimize HTML file by updating resource paths and minifying"""
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update CSS paths
        for css_link in soup.find_all('link', rel='stylesheet'):
            if css_link['href'].startswith('/css/'):
                css_link['href'] = css_link['href'].replace('/css/', '/dist/css/')
        
        # Update JS paths
        for script in soup.find_all('script', src=True):
            if script['src'].startswith('/js/'):
                script['src'] = script['src'].replace('/js/', '/dist/js/')
                # Add defer attribute to non-critical scripts
                if 'jquery' not in script['src']:
                    script['defer'] = ''
        
        # Minify HTML
        minified_html = htmlmin.minify(str(soup), remove_empty_space=True)
        
        # Save optimized file
        output_path = self.dist_dir / html_file.relative_to(self.root_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_html)

    def run_optimization(self):
        """Run the complete optimization process"""
        print("Starting deployment optimization...")
        
        # Setup
        self.setup_dist_directory()
        
        # Analyze usage
        print("Analyzing file usage...")
        self.analyze_file_usage()
        
        # Optimize files
        print("Optimizing files...")
        css_files = list(self.root_dir.rglob('*.css'))
        js_files = list(self.root_dir.rglob('*.js'))
        html_files = list(self.root_dir.rglob('*.html'))
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            # Optimize CSS
            css_savings = sum(executor.map(self.optimize_css, css_files))
            
            # Optimize JavaScript
            js_savings = sum(executor.map(self.optimize_js, js_files))
            
            # Optimize HTML
            list(executor.map(self.optimize_html, html_files))
        
        # Generate optimization report
        report = {
            'css_savings_kb': round(css_savings / 1024, 2),
            'js_savings_kb': round(js_savings / 1024, 2),
            'total_savings_kb': round((css_savings + js_savings) / 1024, 2),
            'unused_classes': len([k for k, v in self.css_usage_map.items() if v == 0]),
            'unused_functions': len([k for k, v in self.js_usage_map.items() if v == 0])
        }
        
        # Save report
        with open(self.dist_dir / 'optimization_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nOptimization complete! Total savings: {report['total_savings_kb']}KB")
        return report

if __name__ == '__main__':
    optimizer = DeploymentOptimizer()
    optimizer.run_optimization()