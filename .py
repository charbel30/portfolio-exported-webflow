from bs4 import BeautifulSoup
import os
import re

def get_platform_name(url):
    """Extract platform name from URL and return appropriate accessible name."""
    url = url.lower()
    if "github.com" in url:
        return "GitHub Profile"
    elif "linkedin.com" in url:
        return "LinkedIn Profile"
    elif "youtube.com" in url or "youtu.be" in url:
        return "YouTube Channel"
    elif "instagram.com" in url:
        return "Instagram Profile"
    elif "x.com" in url or "twitter.com" in url:
        return "X (Twitter) Profile"
    else:
        return "Social Media Profile"

def fix_social_links(html_content):
    """Add accessible names to social media links."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all social links
    social_links = soup.find_all('a', class_='social-link')
    
    for link in social_links:
        # Get the URL
        href = link.get('href', '')
        
        # Generate appropriate accessible name
        accessible_name = get_platform_name(href)
        
        # Add aria-label if it doesn't exist
        if not link.get('aria-label'):
            link['aria-label'] = accessible_name
        
        # If link has no text content, add span with visually hidden text
        if not link.text.strip():
            hidden_text = soup.new_tag('span', attrs={
                'class': 'visually-hidden',
                'style': 'position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;'
            })
            hidden_text.string = accessible_name
            link.append(hidden_text)
    
    return str(soup)

def process_html_files():
    """Process all HTML files in the current directory and subdirectories."""
    # Get the current directory
    current_dir = os.getcwd()
    files_processed = 0
    files_modified = 0
    
    print(f"Starting to process HTML files in {current_dir} and subdirectories...")
    
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                files_processed += 1
                
                try:
                    # Read the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix social links
                    modified_content = fix_social_links(content)
                    
                    # Only write if changes were made
                    if modified_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        files_modified += 1
                        print(f"Modified: {file_path}")
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")

if __name__ == "__main__":
    process_html_files()