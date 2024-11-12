import os
from datetime import datetime
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_sitemap():
    # Base URL of your site - this should be updated to match your production URL
    base_url = "https://charbeltannous.com/"  # Update this to your actual domain
    
    # Initialize sitemap XML
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Walk through all files in the directory
    for root, dirs, files in os.walk('.'):
        # Skip scripts, .github and other non-content directories
        if any(skip in root for skip in ['/scripts', '/.github', '/.git', '/images', '/css', '/js']):
            continue
            
        for file in files:
            if file.endswith('.html'):
                # Get the relative path
                rel_path = os.path.join(root, file)
                # Remove leading ./ if present
                rel_path = rel_path[2:] if rel_path.startswith('./') else rel_path
                
                # Convert index.html to just directory
                if file == 'index.html':
                    rel_path = os.path.dirname(rel_path)
                    if rel_path == '':
                        rel_path = ''  # Root index.html
                
                # Create full URL
                full_url = urljoin(base_url, rel_path)
                
                # Create URL entry
                url = ET.SubElement(urlset, "url")
                loc = ET.SubElement(url, "loc")
                loc.text = full_url
                
                # Add last modified date
                lastmod = ET.SubElement(url, "lastmod")
                lastmod.text = datetime.utcnow().strftime('%Y-%m-%d')
                
                # Add priority (higher for home page)
                priority = ET.SubElement(url, "priority")
                priority.text = "1.0" if rel_path == '' else "0.8"
    
    # Create pretty XML string
    rough_string = ET.tostring(urlset, encoding='unicode')
    pretty_xml = minidom.parseString(rough_string).toprettyxml(indent="  ")
    
    # Write to sitemap.xml
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

if __name__ == "__main__":
    generate_sitemap()
