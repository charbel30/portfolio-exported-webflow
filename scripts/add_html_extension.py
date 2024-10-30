import os
from bs4 import BeautifulSoup

# Directory containing your HTML files
html_dir = '.'

def add_html_extension(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        modified = False

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Skip the root URL and already .html URLs
            if href.startswith('/') and href != '/' and not href.endswith('.html'):
                a_tag['href'] = href + '.html'
                modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        print(f"Updated: {file_path}")
    else:
        print(f"No changes: {file_path}")

def main():
    for root, dirs, files in os.walk(html_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                add_html_extension(file_path)

if __name__ == "__main__":
    main()