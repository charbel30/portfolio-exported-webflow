import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

def optimize_html_file(html_file):
    """Apply performance optimizations to a single HTML file"""
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    # Preload fonts to prevent layout shifts
    font_files = [
        'plusjakartasans-regular.woff',
        'plusjakartasans-light.woff',
        'plusjakartasans-bold.woff',
        'plusjakartasans-medium.woff'
    ]
    
    for font in font_files:
        preload = soup.new_tag('link', rel='preload', href=f'/images/{font}', as_='font', type='font/woff', crossorigin='anonymous')
        soup.head.insert(0, preload)
    
    # Extract and inline critical CSS from webflow-style.css
    css_file = 'css/webflow-style.css'
    if os.path.exists(css_file):
        critical_css = extract_critical_css(html_file, css_file)
        if critical_css:
            # Add critical CSS to head
            style_tag = soup.new_tag('style')
            style_tag.string = critical_css
            soup.head.insert(0, style_tag)
            
            # Add preload for full CSS
            for link in soup.find_all('link', {'rel': 'stylesheet'}):
                if 'webflow-style.css' in link.get('href', ''):
                    link['rel'] = 'preload'
                    link['as'] = 'style'
                    link['onload'] = "this.onload=null;this.rel='stylesheet'"
                    
                    # Add no-JS fallback
                    noscript = soup.new_tag('noscript')
                    fallback_link = soup.new_tag('link', rel='stylesheet', href=link['href'])
                    noscript.append(fallback_link)
                    link.insert_after(noscript)

    # Optimize script loading
    optimize_scripts(soup)
    
    # Add resource hints
    add_resource_hints(soup)
    
    # Add cache control headers
    add_cache_control(soup)

    # Write optimized HTML
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))

def extract_critical_css(html_file, css_file):
    """Extract critical CSS based on above-the-fold content"""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    with open(css_file, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Get elements visible in the first viewport
    critical_selectors = set()
    
    # Extract classes and IDs from critical elements
    critical_elements = soup.select(
        'header, nav, .nav, .navbar, ' +  # Navigation elements
        'main > *:first-child, ' +        # First main content
        '[class*="hero"], ' +             # Hero sections
        '.header, .banner, ' +            # Header/banner areas
        '.preloader-content, ' +          # Preloader
        '.brand, .logo, #logo'            # Logo elements
    )
    
    for element in critical_elements:
        # Add element tag
        critical_selectors.add(element.name)
        
        # Add classes
        if element.get('class'):
            critical_selectors.update(element['class'])
        
        # Add IDs
        if element.get('id'):
            critical_selectors.add(f"#{element['id']}")
        
        # Add parent classes for context
        parent = element.parent
        while parent and parent.name != '[document]':
            if parent.get('class'):
                critical_selectors.update(parent['class'])
            parent = parent.parent
    
    # Extract matching CSS rules
    critical_css = []
    css_rules = re.findall(r'([^{]+){([^}]+)}', css_content)
    
    for selector, rules in css_rules:
        selectors = [s.strip() for s in selector.split(',')]
        
        # Check if any selector matches our critical elements
        for sel in selectors:
            # Basic element selectors
            if sel.strip().lower() in critical_selectors:
                critical_css.append(f"{selector}{{{rules}}}")
                break
                
            # Class selectors
            classes = re.findall(r'\.([\w-]+)', sel)
            if any(c in critical_selectors for c in classes):
                critical_css.append(f"{selector}{{{rules}}}")
                break
                
            # ID selectors
            ids = re.findall(r'#([\w-]+)', sel)
            if any(f"#{i}" in critical_selectors for i in ids):
                critical_css.append(f"{selector}{{{rules}}}")
                break
    
    # Add essential animations and transitions
    animation_rules = re.findall(r'(@keyframes[\s\S]+?}\s*})', css_content)
    critical_css.extend(animation_rules)
    
    return '\n'.join(critical_css)

def optimize_scripts(soup):
    """Optimize script loading to prevent layout shifts"""
    # Move all scripts to end of body
    scripts = soup.find_all('script', src=True)
    for script in scripts:
        # Keep jQuery at the top since it's a dependency
        if 'jquery.js' not in script['src']:
            script.extract()
            soup.body.append(script)
        
        # Add defer to non-critical scripts
        if not any(critical in script['src'] for critical in ['jquery.js', 'webflow-script.js']):
            script['defer'] = ''

def add_resource_hints(soup):
    """Add preload, preconnect, and dns-prefetch hints"""
    head = soup.head
    
    # Preconnect to external domains
    external_domains = {
        'https://cdn.jsdelivr.net',
    }
    
    for domain in external_domains:
        preconnect = soup.new_tag('link', rel='preconnect', href=domain)
        dns_prefetch = soup.new_tag('link', rel='dns-prefetch', href=domain)
        head.insert(0, preconnect)
        head.insert(1, dns_prefetch)
    
    # Preload critical resources
    critical_resources = [
        ('js/jquery.js', 'script'),
        ('js/webflow-script.js', 'script')
    ]
    
    for path, type_ in critical_resources:
        if os.path.exists(path):
            preload = soup.new_tag('link', rel='preload', href=f'/{path}', as_=type_)
            head.insert(0, preload)

def add_cache_control(soup):
    """Add cache control headers via meta tags"""
    cache_meta = soup.new_tag('meta', attrs={
        'http-equiv': 'Cache-Control',
        'content': 'max-age=31536000'
    })
    soup.head.insert(0, cache_meta)

def main():
    # Process all HTML files
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.html'):
                html_file = os.path.join(root, file)
                print(f"Optimizing {html_file}")
                optimize_html_file(html_file)

if __name__ == '__main__':
    main()
    above_fold_parents = [
        'header', 'nav', '.nav', '.navbar',
        'main > *:first-child',
        '[class*="hero"]',
        '.header', '.banner'
    ]
    
    for parent_selector in above_fold_parents:
        if element.find_parent(parent_selector):
            return True
    
    # Check if element is one of the first few elements in the body
    body = element.find_parent('body')
    if body:
        first_elements = body.find_all(['div', 'section', 'header', 'nav'], limit=3)
        return element in first_elements or any(element in el.descendants for el in first_elements)
    
    return False

def main():
    # Process all HTML files
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.html'):
                html_file = os.path.join(root, file)
                print(f"Optimizing {html_file}")
                optimize_html_file(html_file)

if __name__ == '__main__':
    main()
