import os
import requests
from bs4 import BeautifulSoup

# Directory containing your HTML files
html_dir = '.'

def check_url(url):
    try:
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            print(f"SUCCESS: {url} -> {response.url}")
        else:
            print(f"ERROR {response.status_code}: {url}")
    except requests.exceptions.RequestException as e:
        print(f"FAILED: {url} - {e}")

def extract_and_check_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                url = f"http://127.0.0.1:5500{href}"
                check_url(url)

def main():
    for root, dirs, files in os.walk(html_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                extract_and_check_links(file_path)

if __name__ == "__main__":
    main()