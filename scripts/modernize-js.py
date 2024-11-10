import os
from pathlib import Path
import re
import json
from bs4 import BeautifulSoup

class JavaScriptModernizer:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir)
        self.modern_features = {
            'optional_chaining': r'\?\.',
            'nullish_coalescing': r'\?\?',
            'async_await': r'async|await',
            'arrow_functions': r'=>',
            'destructuring': r'(?:const|let|var)\s*\{[^}]+\}\s*=',
            'spread_operator': r'\.{3}',
            'template_literals': r'`[^`]*`'
        }
        
    def analyze_browser_support(self, js_content):
        """Analyze JavaScript content for modern features usage"""
        features_used = {}
        for feature, pattern in self.modern_features.items():
            if re.search(pattern, js_content):
                features_used[feature] = True
        return features_used
    
    def generate_fallback(self, js_content):
        """Generate fallback code for older browsers"""
        # Replace optional chaining
        js_content = re.sub(
            r'(\w+)\?\.(\w+)',
            r'\1 && \1.\2',
            js_content
        )
        
        # Replace nullish coalescing
        js_content = re.sub(
            r'(\w+)\s*\?\?\s*([^;]+)',
            r'(\1 !== null && \1 !== undefined) ? \1 : \2',
            js_content
        )
        
        # Replace arrow functions
        js_content = re.sub(
            r'(\([^)]*\))\s*=>\s*({[\s\S]*?})',
            r'function\1 \2',
            js_content
        )
        
        # Simple arrow functions without braces
        js_content = re.sub(
            r'(\([^)]*\))\s*=>\s*([^{].*?)(?=[,;]|$)',
            r'function\1 { return \2; }',
            js_content
        )
        
        return js_content
    
    def add_polyfills(self, features_used):
        """Generate necessary polyfills based on features used"""
        polyfills = []
        
        if features_used.get('optional_chaining'):
            polyfills.append("""
                if (!Object.prototype.optionalChaining) {
                    Object.prototype.optionalChaining = function(path) {
                        let obj = this;
                        for (let key of path.split('.')) {
                            if (obj === null || obj === undefined) return undefined;
                            obj = obj[key];
                        }
                        return obj;
                    };
                }
            """)
        
        if features_used.get('nullish_coalescing'):
            polyfills.append("""
                if (typeof window.nullishCoalesce !== 'function') {
                    window.nullishCoalesce = function(value, fallback) {
                        return value !== null && value !== undefined ? value : fallback;
                    };
                }
            """)
        
        return '\n'.join(polyfills)
    
    def generate_module_bundle(self, js_content, features):
        """Generate a modern/legacy bundle with appropriate loading"""
        modern_bundle = js_content
        legacy_bundle = self.generate_fallback(js_content)
        polyfills = self.add_polyfills(features)
        
        # Create module/nomodule script loading
        bundle = {
            'modern': modern_bundle,
            'legacy': polyfills + '\n' + legacy_bundle
        }
        
        return bundle
    
    def process_file(self, js_file):
        """Process a single JavaScript file"""
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analyze features
        features = self.analyze_browser_support(content)
        
        # Generate bundles
        bundles = self.generate_module_bundle(content, features)
        
        # Save modern bundle
        modern_path = js_file.parent / f"{js_file.stem}.modern{js_file.suffix}"
        with open(modern_path, 'w', encoding='utf-8') as f:
            f.write(bundles['modern'])
        
        # Save legacy bundle
        legacy_path = js_file.parent / f"{js_file.stem}.legacy{js_file.suffix}"
        with open(legacy_path, 'w', encoding='utf-8') as f:
            f.write(bundles['legacy'])
        
        return {
            'file': str(js_file),
            'features_detected': features,
            'modern_bundle': str(modern_path),
            'legacy_bundle': str(legacy_path)
        }
    
    def update_html_references(self, html_file, js_stats):
        """Update HTML files to use appropriate script bundles"""
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all script tags
        script_tags = soup.find_all('script', src=True)
        
        # Create new script tags list
        new_scripts = []
        
        # Process each script tag
        for script in script_tags:
            src = script['src']
            if src.endswith('.js'):
                # Find corresponding stats
                for stat in js_stats:
                    if src in stat['file']:
                        # Create modern script tag
                        modern_script = soup.new_tag('script')
                        modern_script['type'] = 'module'
                        modern_script['src'] = src.replace('.js', '.modern.js')
                        new_scripts.append(modern_script)
                        
                        # Create legacy script tag
                        legacy_script = soup.new_tag('script')
                        legacy_script['nomodule'] = ''
                        legacy_script['src'] = src.replace('.js', '.legacy.js')
                        new_scripts.append(legacy_script)
                        
                        # Remove original script tag
                        script.decompose()
                        break
        
        # Add new script tags to the head
        for new_script in new_scripts:
            soup.head.append(new_script)
        
        # Save updated HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    def run(self):
        """Run the complete modernization process"""
        print("Starting JavaScript modernization...")
        
        # Process all JavaScript files
        js_files = list(self.root_dir.rglob('*.js'))
        js_stats = []
        
        for js_file in js_files:
            if not any(x in str(js_file) for x in ['.modern.js', '.legacy.js']):
                print(f"Processing {js_file}...")
                stats = self.process_file(js_file)
                js_stats.append(stats)
        
        # Update HTML files
        html_files = list(self.root_dir.rglob('*.html'))
        for html_file in html_files:
            print(f"Updating {html_file}...")
            self.update_html_references(html_file, js_stats)
        
        # Save optimization report
        report = {
            'files_processed': len(js_stats),
            'feature_usage': {},
            'bundles_generated': len(js_stats) * 2  # modern + legacy for each file
        }
        
        # Aggregate feature usage
        for stat in js_stats:
            for feature, used in stat['features_detected'].items():
                if used:
                    report['feature_usage'][feature] = report['feature_usage'].get(feature, 0) + 1
        
        with open(self.root_dir / 'js-modernization-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\nModernization complete! Check js-modernization-report.json for details.")
        return report

if __name__ == '__main__':
    modernizer = JavaScriptModernizer()
    stats = modernizer.run()
    print("\nModernization Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
