
import os
from bs4 import BeautifulSoup

def inline_critical_css_js(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Inline critical CSS
    for link in soup.find_all('link', {'rel': 'stylesheet'}):
        if 'critical' in link.get('href', ''):
            css_file = link['href']
            with open(css_file, 'r', encoding='utf-8') as css:
                style_tag = soup.new_tag('style')
                style_tag.string = css.read()
                link.replace_with(style_tag)

    # Defer non-critical scripts
    for script in soup.find_all('script', {'src': True}):
        if 'critical' not in script['src']:
            script['defer'] = 'defer'

    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))

def main():
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.html'):
                inline_critical_css_js(os.path.join(root, file))

if __name__ == '__main__':
    main()