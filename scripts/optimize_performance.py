import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import cssselect
import tinycss

def extract_critical_css(html_file, css_file):
    """Extract critical CSS by analyzing above-the-fold content"""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    with open(css_file, 'r', encoding='utf-8') as f:
        full_css = f.read()
    
    # Get elements visible in the first viewport
    critical_elements = set()
    
    # Header, navigation, and hero section are typically above the fold
    viewport_elements = soup.select(
        'header, nav, .nav, .navbar, ' +  # Navigation elements
        'main > *:first-child, ' +        # First main content
        '[class*="hero"], ' +             # Hero sections
        '.header, .banner, ' +            # Header/banner areas
        'img:first-of-type, ' +          # First image
        '.logo, #logo'                    # Logo elements
    )
    
    # Collect all classes and IDs from viewport elements
    for element in viewport_elements:
        # Add element tag
        critical_elements.add(element.name)
        
        # Add classes
        if element.get('class'):
            critical_elements.update(element['class'])
        
        # Add IDs
        if element.get('id'):
            critical_elements.add(f"#{element['id']}")
        
        # Add parent classes for context
        parent = element.parent
        while parent and parent.name != '[document]':
            if parent.get('class'):
                critical_elements.update(parent['class'])
            parent = parent.parent
    
    # Parse the full CSS
    critical_css_rules = []
    css_rules = re.findall(r'([^{]+){([^}]+)}', full_css)
    
    for selector, rules in css_rules:
        selectors = [s.strip() for s in selector.split(',')]
        
        # Check if any selector matches our critical elements
        for sel in selectors:
            # Basic element selectors
            if sel.strip().lower() in critical_elements:
                critical_css_rules.append(f"{selector}{{{rules}}}")
                break
                
            # Class selectors
            classes = re.findall(r'\.([\w-]+)', sel)
            if any(c in critical_elements for c in classes):
                critical_css_rules.append(f"{selector}{{{rules}}}")
                break
                
            # ID selectors
            ids = re.findall(r'#([\w-]+)', sel)
            if any(f"#{i}" in critical_elements for i in ids):
                critical_css_rules.append(f"{selector}{{{rules}}}")
                break
    
    # Add essential animations and transitions
    animation_rules = re.findall(r'(@keyframes[\s\S]+?}\s*})', full_css)
    critical_css_rules.extend(animation_rules)
    
    return '\n'.join(critical_css_rules)

def optimize_html_file(html_file):
    """Apply performance optimizations to a single HTML file"""
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
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

    # Defer non-critical scripts
    for script in soup.find_all('script', {'src': True}):
        if not any(critical in script['src'] for critical in ['jquery.js', 'webflow-script.js']):
            script['defer'] = 'defer'

    # Add resource hints
    add_resource_hints(soup)
    
    # Optimize images
    optimize_images(soup)
    
    # Add cache control headers
    add_cache_control(soup)

    # Write optimized HTML
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))

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

def optimize_images(soup):
    """Add responsive image attributes and optimize image loading"""
    for img in soup.find_all('img'):
        # Add loading="lazy" for images below the fold
        if not is_above_fold(img):
            img['loading'] = 'lazy'
        
        # Add srcset for responsive images
        if img.get('src') and img.get('src').endswith(('.jpg', '.jpeg', '.png', '.webp')):
            src = img['src'].lstrip('/')
            base_path = os.path.splitext(src)[0]
            dir_path = os.path.dirname(src)
            
            # Check for responsive image variants
            responsive_sizes = ['500', '800', '1080', '1600']
            srcset = []
            
            for size in responsive_sizes:
                variant_path = f"{base_path}-p-{size}{os.path.splitext(src)[1]}"
                if os.path.exists(variant_path):
                    srcset.append(f"{variant_path} {size}w")
            
            if srcset:
                img['srcset'] = ', '.join(srcset)
                img['sizes'] = '(max-width: 500px) 500px, (max-width: 800px) 800px, 1080px'

def add_cache_control(soup):
    """Add cache control headers via meta tags"""
    cache_meta = soup.new_tag('meta', attrs={
        'http-equiv': 'Cache-Control',
        'content': 'max-age=31536000'
    })
    soup.head.insert(0, cache_meta)

def is_above_fold(element):
    """Determine if an element is likely above the fold"""
    # Check if element is within typical above-fold elements
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
